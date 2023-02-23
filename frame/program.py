import subprocess
import os
import signal
from typing import Union

default_wait_timeout = 10

Command = Union[str, list[str]]

def format_output(name: str, output: str) -> str:
    '''
    After collecting a program's output into a string, this function wraps it in a border for easy
    reading
    '''
    l_pad = 36 - len(name) // 2
    r_pad = l_pad
    if len(name) % 2 == 1:
        r_pad -= 1
    l_pad = max(l_pad, 1)
    r_pad = max(r_pad, 1)
    header = '─' * l_pad + '┤ ' + name + ' ├' + '─' * r_pad
    divider = '\n│'
    body = divider.join(' ' + line for line in output.strip().splitlines())
    footer = '─' * 78
    return '╭' + header + divider + body + '\n╰' + footer

class Program:
    def __init__(self, command: Command, env: dict[str, str] = {}):
        if isinstance(command, str):
            self.command = [command]
        else:
            self.command = command
        self.env = os.environ | env
        self.name = self.command[0]
        self.process = subprocess.Popen(
            self.command,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True,
            preexec_fn=os.setsid)
        # Without setsid killing the subprocess doesn't kill the whole process tree,
        # see https://pymotw.com/2/subprocess/#process-groups-sessions
        self.output = ''
        self.killed = False

    def assert_running(self) -> None:
        if self.process.poll() is not None:
            try:
                self.wait()
            except:
                pass
            assert False, self.name + ' is dead'

    def wait(self, timeout=default_wait_timeout) -> None:
        raw_output, _ = self.process.communicate(timeout=timeout)
        self.output = raw_output.decode('utf-8').strip()
        print('\n' + format_output(self.name, self.output))
        if self.process.returncode != 0:
            message = self.name
            if self.killed:
                message += ' refused to terminate'
            else:
                message += ' closed with exit code ' + str(self.process.returncode)
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

    def __enter__(self) -> 'Program':
        return self

    def __exit__(self, *args):
        if self.process.returncode == None:
            self.assert_running()
            try:
                self.kill()
            except:
                pass
