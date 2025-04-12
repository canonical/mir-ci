import asyncio
import os
import re
import subprocess
import time
from typing import Any, Dict, Optional, Tuple

import inotify.adapters
import yaml

from ..interfaces.benchmarkable import Benchmarkable
from ..lib.cgroups import Cgroup
from ..program.app import App, AppType
from ..program.program import Program

display_appear_timeout = 10
min_mir_run_time = 0.1


SERVER_MODE_RE = re.compile(r"Current mode ([0-9x]+ [0-9.]+Hz)")
SERVER_RENDERER_RE = re.compile(r"GL renderer: (.*)$", re.MULTILINE)


def clear_wayland_display(runtime_dir: str, name: str) -> None:
    # Clear out any existing display before waiting for the new one
    for path in [os.path.join(runtime_dir, name), os.path.join(runtime_dir, name + ".lock")]:
        if os.path.exists(path):
            os.remove(path)


def wait_for_wayland_display(runtime_dir: str, name: str) -> None:
    i = inotify.adapters.Inotify()
    i.add_watch(runtime_dir, mask=inotify.constants.IN_CREATE)
    # Check if display has already appeared Since we've already created the watch it might be seen
    # by both this check and inotify, but there's no way it's seen by neither.
    if os.path.exists(os.path.join(runtime_dir, name)):
        return
    # Wait for display to appear
    for event in i.event_gen(timeout_s=display_appear_timeout, yield_nones=False):
        (_, type_names, path, filename) = event
        if filename == name:
            return
    raise RuntimeError("Wayland display " + name + " did not appear")


class DisplayServer(Benchmarkable):
    server: Optional[Program] = None

    def __init__(self, app: App, add_extensions: Tuple[str, ...] = (), env: Dict[str, str] = {}) -> None:
        self.app: App = app
        # Snaps require the display to be in the form "waland-<number>". The 00 prefix lets us
        # easily identify displays created by this test suit and remove them in bulk if a bunch
        # don't get cleaned up properly.
        self.display_name = self.get_wayland_display()
        self.env: Dict[str, str] = env
        self.env["WAYLAND_DISPLAY"] = self.display_name
        self.env["MIR_SERVER_ADD_WAYLAND_EXTENSIONS"] = ":".join(add_extensions)

    async def get_cgroup(self) -> Cgroup:
        assert self.server
        return await self.server.get_cgroup()

    def program(self, app: App, env: Dict[str, str] = {}) -> Program:
        return Program(
            app, env=dict({"DISPLAY": "no", "QT_QPA_PLATFORM": "wayland", "WAYLAND_DISPLAY": self.display_name}, **env)
        )

    def record_properties(self, fixture) -> None:
        assert self.server
        if m := SERVER_MODE_RE.search(self.server.output):
            fixture("server_mode", m.group(1))
        if m := SERVER_RENDERER_RE.search(self.server.output):
            fixture("server_renderer", m.group(1))

    async def __aenter__(self) -> "DisplayServer":
        runtime_dir = os.environ["XDG_RUNTIME_DIR"]
        clear_wayland_display(runtime_dir, self.display_name)
        self.server = await Program(self.app, env=self.env).__aenter__()
        try:
            wait_for_wayland_display(runtime_dir, self.display_name)
        except Exception as e:
            await self.server.kill()
            raise e
        self.start_time = time.time()
        return self

    async def __aexit__(self, *args):
        # If Mir is run for too short a period of time it tends to not shut down correctly
        # See https://github.com/canonical/mir/issues/2845
        sleep_time = self.start_time + min_mir_run_time - time.time()
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
        assert self.server
        await self.server.kill()

    @staticmethod
    def get_wayland_display() -> str:
        return "wayland-00" + str(os.getpid())


class DisplayServerWithDisplayConfig:
    def __init__(self, local_server):
        self.local_server = local_server
        self.cmd_wrapper = (
            (lambda x: ["snap", "run", "--shell", local_server.command[0], "-c", " ".join(x)])
            if local_server.app_type == AppType.snap
            else lambda x: x
        )
        self.tmp_filename = subprocess.check_output(self.cmd_wrapper(["mktemp"]), encoding="utf-8").strip()
        subprocess.check_output(self.cmd_wrapper(["rm", self.tmp_filename]), encoding="utf-8").strip()
        self.server = DisplayServer(self.local_server, env={"MIR_SERVER_DISPLAY_CONFIG": f"static={self.tmp_filename}"})

    async def __aenter__(self) -> "DisplayServerWithDisplayConfig":
        await self.server.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self.server.__aexit__(*args)

    def read_config(self) -> Any:
        content = subprocess.check_output(
            self.cmd_wrapper(["cat", self.tmp_filename]),
            encoding="utf-8",
        )
        # the yaml parser doesn't like tabs before our comments
        return yaml.safe_load(content.replace("\t#", "  #"))

    def write_config(self, content: Any) -> None:
        subprocess.run(
            self.cmd_wrapper(["tee", self.tmp_filename]),
            encoding="utf-8",
            input=yaml.dump(content),
            capture_output=True,
            check=True,
        )
