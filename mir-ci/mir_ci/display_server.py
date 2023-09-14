import inotify.adapters
import os
import time
import asyncio

from typing import Dict, Tuple, Callable

from mir_ci.program import Program, Command
from mir_ci.benchmarker import Benchmarker, benchmarker_preexec_fn

display_appear_timeout = 10
min_mir_run_time = 0.1

def clear_wayland_display(runtime_dir: str, name: str) -> None:
    # Clear out any existing display before waiting for the new one
    for path in [
        os.path.join(runtime_dir, name),
        os.path.join(runtime_dir, name + '.lock')
    ]:
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
    raise RuntimeError('Wayland display ' + name + ' did not appear')

class DisplayServer:
    def __init__(self, command: Command, add_extensions: Tuple[str, ...] = (), benchmark: bool = False) -> None:
        self.command = command
        self.add_extensions = add_extensions
        # Snaps require the display to be in the form "waland-<number>". The 00 prefix lets us
        # easily identify displays created by this test suit and remove them in bulk if a bunch
        # don't get cleaned up properly.
        self.display_name = 'wayland-00' + str(os.getpid())
        self.benchmarker = Benchmarker() if benchmark is True else None

    def _preexec_func(self, process_name: str):
        if self.benchmarker:
            benchmarker_preexec_fn(process_name)

    def program(self, command: Command, env: Dict[str, str] = {}) -> Program:
        return Program(command, env=dict({
                'DISPLAY': 'no',
                'QT_QPA_PLATFORM': 'wayland',
                'WAYLAND_DISPLAY': self.display_name
            },
            **env),
            preexec_fn=lambda: self._preexec_func("application")
        )

    async def __aenter__(self) -> 'DisplayServer':
        runtime_dir = os.environ['XDG_RUNTIME_DIR']
        clear_wayland_display(runtime_dir, self.display_name)
        self.server = await Program(
            self.command, 
            env={
                'WAYLAND_DISPLAY': self.display_name,
                'MIR_SERVER_ADD_WAYLAND_EXTENSIONS': ':'.join(self.add_extensions),
            },
            preexec_fn=lambda: self._preexec_func("compositor")
        ).__aenter__()
        try:
            wait_for_wayland_display(runtime_dir, self.display_name)
            if self.benchmarker:
                self.benchmarker.start()
        except:
            await self.server.kill()
            if self.benchmarker:
                await self.benchmarker.stop()
            raise
        self.start_time = time.time()
        return self

    async def __aexit__(self, *args):
        # If Mir is run for too short a period of time it tends to not shut down correctly
        # See https://github.com/MirServer/mir/issues/2845
        sleep_time = self.start_time + min_mir_run_time - time.time()
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
        await self.server.kill()
        if self.benchmarker:
            await self.benchmarker.stop()

    def generate_report(self, record_property: Callable[[str, object], None]) -> None:
        if self.benchmarker:
            idx = 0
            for item in self.benchmarker.get_data():
                # TODO: I should probably output multiple values here instead dof one big JSON blob
                record_property(f"{item.name}_pid", item.pid)
                record_property(f"{item.name}_avg_cpu_percent", item.avg_cpu_percent)
                record_property(f"{item.name}_max_mem_bytes", item.max_mem_bytes)
                record_property(f"{item.name}_avg_mem_bytes", item.avg_mem_bytes)
                idx = idx + 1