from unittest import TestCase
import subprocess
import time

class Program:
    def __init__(self, name: str, args: list[str] = []):
        self.name = name
        self.process = subprocess.Popen(
            [name] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        self.output = ''

    def kill(self) -> None:
        self.process.terminate()
        try:
            raw_output, _ = self.process.communicate(timeout=1)
            had_to_kill = False
        except subprocess.TimeoutExpired:
            self.process.kill()
            raw_output, _ = self.process.communicate()
            had_to_kill = True
        self.output = raw_output.decode('utf-8').strip()
        if self.process.returncode != 0:
            message = self.name
            if had_to_kill:
                message += ' refused to terminate'
            else:
                message += ' closed with exit code ' + str(self.process.returncode)
            if self.output:
                message += ':\n' + self.output
            else:
                message += ' and no output'
            raise RuntimeError(message)

class FrameTestCase(TestCase):
    def setUp(self) -> None:
        self.frame = Program('ubuntu-frame')
        time.sleep(0.5)

    def tearDown(self) -> None:
        self.frame.kill()
