from unittest import TestCase
import inotify.adapters
import subprocess
import os
import time
import signal

long_timeout = 10
min_frame_run_time = 0.1

class Program:
    def __init__(self, name: str, args: list[str] = []):
        self.name = name
        self.process = subprocess.Popen(
            [name] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True,
            preexec_fn=os.setsid)
        # Without setsid killing the subprocess doesn't kill the whole process tree,
        # see https://pymotw.com/2/subprocess/#process-groups-sessions
        self.output = ''
        self.killed = False

    def assert_running(self) -> None:
        assert self.process.poll() is None, self.name + ' is dead'

    def wait(self, timeout=long_timeout) -> None:
        raw_output, _ = self.process.communicate(timeout=timeout)
        self.output = raw_output.decode('utf-8').strip()
        if self.process.returncode != 0:
            message = self.name
            if self.killed:
                message += ' refused to terminate'
            else:
                message += ' closed with exit code ' + str(self.process.returncode)
            if self.output:
                message += ':\n\n' + self.output
            else:
                message += ' and no output'
            raise RuntimeError(message)

    def kill(self) -> None:
        if self.process.returncode == None:
            os.killpg(self.process.pid, signal.SIGTERM)
            try:
                self.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
        if self.process.returncode == None:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.killed = True
            self.wait()

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
    for event in i.event_gen(timeout_s=long_timeout, yield_nones=False):
        (_, type_names, path, filename) = event
        if filename == name:
            return
    # Raise timeout error if we didn't return
    raise RuntimeError('Wayland display ' + name + ' did not appear')

class FrameTestCase(TestCase):
    def setUp(self) -> None:
        wayland_display = 'wayland-99'
        os.environ['WAYLAND_DISPLAY'] = wayland_display
        self.frame = Program('ubuntu-frame')
        self.programs: list[Program] = []
        try:
            wait_for_wayland_display(wayland_display)
        except:
            self.frame.kill()
            raise
        self.start_time = time.time()

    def program(self, name: str, args: list[str] = []) -> Program:
        program = Program(name, args)
        self.programs.append(program)
        return program

    def tearDown(self) -> None:
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
