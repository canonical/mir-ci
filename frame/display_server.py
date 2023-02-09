import inotify.adapters
import os
import time

from program import Program, Command

display_appear_timeout = 10
min_frame_run_time = 0.1

def wait_for_wayland_display(name: str) -> None:
    runtime_dir = os.environ['XDG_RUNTIME_DIR']
    # Clear out any existing display before waiting for the new one
    for path in [
        os.path.join(runtime_dir, name),
        os.path.join(runtime_dir, name + '.lock')
    ]:
        if os.path.exists(path):
            os.remove(path)
    # Set up inotify
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
    # Raise timeout error if we didn't return
    raise RuntimeError('Wayland display ' + name + ' did not appear')

class DisplayServer:
    def __init__(self, command: Command) -> None:
        self.command = command

    def program(self, command: Command) -> Program:
        program = Program(command)
        self.programs.append(program)
        return program

    def __enter__(self) -> 'DisplayServer':
        wayland_display = 'wayland-99'
        os.environ['WAYLAND_DISPLAY'] = wayland_display
        self.frame = Program(self.command)
        self.programs: list[Program] = []
        try:
            wait_for_wayland_display(wayland_display)
        except:
            self.frame.kill()
            raise
        self.start_time = time.time()
        os.environ['QT_QPA_PLATFORM'] = 'wayland'
        return self

    def __exit__(self, *args):
        # If frame is run for too short a period of time it tends to not shut down correctly
        # TODO: fix frame
        sleep_time = self.start_time + min_frame_run_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        for program in self.programs:
            try:
                program.kill()
            except:
                pass
        self.frame.kill()
