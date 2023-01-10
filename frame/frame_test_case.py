from unittest import TestCase
import subprocess
import os
import time

long_timeout = 10
min_frame_run_time = 0.1

class Program:
    def __init__(self, name: str, args: list[str] = []):
        self.name = name
        self.process = subprocess.Popen(
            [name] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        self.output = ''
        self.killed = False

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
            self.process.terminate()
            try:
                self.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
        if self.process.returncode == None:
            self.process.kill()
            self.killed = True
            self.wait()

class FrameTestCase(TestCase):
    def setUp(self) -> None:
        os.environ['WAYLAND_DISPLAY'] = 'wayland-99'
        self.frame = Program('ubuntu-frame')
        try:
            inotify = Program('inotifywait', ['--event', 'create', os.environ['XDG_RUNTIME_DIR']])
            inotify.wait()
        except:
            self.frame.kill()
            raise
        self.start_time = time.time()

    def tearDown(self) -> None:
        # If frame is run for too short a period of time it tends to not shut down correctly
        # TODO: fix frame
        sleep_time = self.start_time + min_frame_run_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.frame.kill()
