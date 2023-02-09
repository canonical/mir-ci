import subprocess
import os
import signal

default_wait_timeout = 10

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

    def wait(self, timeout=default_wait_timeout) -> None:
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
