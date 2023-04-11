import os
import signal
from typing import Dict, List, Tuple, Union, Optional
import asyncio

default_wait_timeout = default_term_timeout = 10

Command = Union[str, List[str], Tuple[str, ...]]

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
    def __init__(self, command: Command, env: Dict[str, str] = {}):
        if isinstance(command, str):
            self.command: tuple[str, ...] = (command,)
        else:
            self.command = tuple(command)
        self.name = self.command[0]
        self.env = env
        self.process: Optional[asyncio.subprocess.Process] = None
        self.output = ''
        self.waited_for = False
        self.killed = False

    def assert_running(self) -> None:
        assert self.process and self.process.returncode is None, self.name + ' is dead'

    async def wait(self) -> None:
        assert self.process
        raw_output, _ = await self.process.communicate()
        self.waited_for = True
        self.output = raw_output.decode('utf-8').strip()
        print('\n' + format_output(self.name, self.output))
        if self.process.returncode != 0:
            message = self.name
            if self.killed:
                message += ' refused to terminate'
            else:
                message += ' closed with exit code ' + str(self.process.returncode)
            raise RuntimeError(message)

    async def kill(self, timeout=default_term_timeout) -> None:
        assert self.process
        if not self.waited_for:
            os.killpg(self.process.pid, signal.SIGTERM)
            try:
                await asyncio.wait_for(self.wait(), timeout=timeout)
            except asyncio.exceptions.TimeoutError:
                pass
        if not self.waited_for:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.killed = True
            try:
                await asyncio.wait_for(self.wait(), timeout=1)
            except asyncio.exceptions.TimeoutError:
                raise RuntimeError('failed to kill ' + self.name)

    async def __aenter__(self) -> 'Program':
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            env=dict(os.environ, **self.env),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            close_fds=True,
            preexec_fn=os.setsid)
        # Without setsid killing the subprocess doesn't kill the whole process tree,
        # see https://pymotw.com/2/subprocess/#process-groups-sessions
        # Without setsid killing the subprocess doesn't kill the whole process tree,
        # see https://pymotw.com/2/subprocess/#process-groups-sessions
        return self

    async def __aexit__(self, *args):
        if not self.waited_for:
            self.assert_running()
            try:
                await self.kill()
            except:
                pass
