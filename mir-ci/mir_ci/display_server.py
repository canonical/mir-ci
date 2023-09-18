import inotify.adapters
import os
import time
import asyncio

from typing import Dict, Tuple, Callable, Literal, Optional

from mir_ci.program import Program, Command

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
    def __init__(
            self,
            command: Command,
            add_extensions: Tuple[str, ...] = (),
            on_program_started: Optional[Callable[[int, str], None]] = None) -> None:
        self.command = command
        self.add_extensions = add_extensions
        # Snaps require the display to be in the form "waland-<number>". The 00 prefix lets us
        # easily identify displays created by this test suit and remove them in bulk if a bunch
        # don't get cleaned up properly.
        self.display_name = 'wayland-00' + str(os.getpid())
        self.on_program_started = on_program_started

    def _on_program_started(self, pid: int, name: str) -> None:
        if self.on_program_started is not None:
            self.on_program_started(pid, name)

    def program(self, command: Tuple[Command, Literal["snap", "deb", "pip"]], env: Dict[str, str] = {}) -> Program:
        def on_started(pid: int):
            self._on_program_started(pid, "application")

        return Program(command[0], env=dict({
                'DISPLAY': 'no',
                'QT_QPA_PLATFORM': 'wayland',
                'WAYLAND_DISPLAY': self.display_name
            },
            **env),
            on_started=on_started,
            systemd_slice=f"mirci-{time.time()}" if command[1] != "snap" else None)

    async def __aenter__(self) -> 'DisplayServer':
        def on_started(pid: int):
            self._on_program_started(pid, "compositor")

        runtime_dir = os.environ['XDG_RUNTIME_DIR']
        clear_wayland_display(runtime_dir, self.display_name)
        self.server = await Program(
            self.command, 
            env={
                'WAYLAND_DISPLAY': self.display_name,
                'MIR_SERVER_ADD_WAYLAND_EXTENSIONS': ':'.join(self.add_extensions),
            },
            on_started=on_started
        ).__aenter__()
        try:
            wait_for_wayland_display(runtime_dir, self.display_name)
        except:
            await self.server.kill()
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
            
