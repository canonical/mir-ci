import asyncio
import logging
import os
import signal
import uuid
from pathlib import Path
from typing import Awaitable, Dict, List, Optional, Tuple, Union

from mir_ci.interfaces.benchmarkable import Benchmarkable
from mir_ci.lib.cgroups import Cgroup
from mir_ci.program.app import AppType

from .app import App

logger = logging.getLogger(__name__)

default_wait_timeout = default_term_timeout = 10

Command = Union[str, List[str], Tuple[str, ...]]


def format_output(name: str, output: str) -> str:
    """
    After collecting a program's output into a string, this function wraps it in a border for easy
    reading
    """
    l_pad = 37 - len(name) // 2
    r_pad = l_pad
    if len(name) % 2 == 1:
        r_pad -= 1
    l_pad = max(l_pad, 1)
    r_pad = max(r_pad, 1)
    header = "─" * l_pad + "┤ " + name + " ├" + "─" * r_pad
    divider = "\n│"
    body = divider.join(" " + line for line in output.strip().splitlines())
    footer = "─" * 78
    return "╭" + header + divider + body + "\n╰" + footer


class ProgramError(RuntimeError):
    pass


class Program(Benchmarkable):
    def __init__(self, app: App, env: Dict[str, str] = {}):
        if isinstance(app.command, str):
            self.command: tuple[str, ...] = (app.command,)
        else:
            self.command = tuple(app.command)
        self.app_type = app.app_type

        self.name = self.command[0]
        self.env = env
        self.process: Optional[asyncio.subprocess.Process] = None
        self.process_end: Optional[Awaitable[None]] = None
        self.send_signals_task: Optional[asyncio.Task[None]] = None
        self.cgroups_task: Optional[asyncio.Task[Cgroup]] = None
        self.output = ""
        self.sigkill_sent = False

    def is_running(self) -> bool:
        return self.process is not None and self.process.returncode is None

    async def get_cgroup(self) -> Cgroup:
        assert self.cgroups_task is not None, "Cgroup task is None, is cgroupv2 supported?"
        await self.cgroups_task
        return self.cgroups_task.result()

    async def send_kill_signals(self, timeout: int, term_timeout: int) -> None:
        """Assigned to self.send_signals_task, cancelled when process ends"""
        assert self.is_running(), self.name + " is dead"
        if timeout:
            await asyncio.sleep(timeout)
        assert self.process
        os.killpg(self.process.pid, signal.SIGTERM)
        await asyncio.sleep(term_timeout)
        self.sigkill_sent = True
        os.killpg(self.process.pid, signal.SIGKILL)
        await asyncio.sleep(1)
        # Should have been cancelled by now
        raise ProgramError("failed to kill " + self.name)

    async def wait(self, timeout=default_wait_timeout, term_timeout=default_term_timeout) -> None:
        if self.is_running():
            self.send_signals_task = asyncio.create_task(self.send_kill_signals(timeout, term_timeout))
        if self.process_end is not None:
            await self.process_end
            self.process_end = None
            print("\n" + format_output(self.name, self.output))
            assert self.process
            if self.process.returncode != 0:
                message = self.name
                if self.sigkill_sent:
                    message += " refused to terminate"
                else:
                    message += " closed with exit code " + str(self.process.returncode)
                raise ProgramError(message)

    async def kill(self, timeout=default_term_timeout) -> None:
        try:
            await self.wait(0, timeout)
        except ProgramError:
            pass

    async def __aenter__(self) -> "Program":
        command = tuple(str(arg) for arg in self.command)
        if self.app_type != AppType.snap:
            scope = f"mirci-{uuid.uuid4()}.scope"
            prefix = ("systemd-run", "--user", "--quiet", "--scope", f"--unit={scope}")
            command = (*prefix, *command)
            # TODO: the global `env` and `xdg` marks should be amended with
            # app-local ones, so different programs can get different environments.
            env = dict(os.environ, **self.env)
        else:
            env = dict(
                {
                    k: v
                    for k, v in os.environ.items()
                    if k in ("DISPLAY", "XAUTHORITY", "PATH", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS")
                    or k.startswith("MIR_SERVER_")
                },
                **self.env,
            )
        process = await asyncio.create_subprocess_exec(
            *command,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            close_fds=True,
            preexec_fn=os.setsid,
        )

        # Without setsid killing the subprocess doesn't kill the whole process tree,
        # see https://pymotw.com/2/subprocess/#process-groups-sessions
        async def communicate() -> None:
            raw_output, _ = await process.communicate()
            if self.send_signals_task is not None and not self.send_signals_task.done():
                self.send_signals_task.cancel()
            self.output = raw_output.decode("utf-8").strip()

        self.process = process
        self.process_end = communicate()
        if Path("/sys/fs/cgroup/cgroup.controllers").exists():
            self.cgroups_task = Cgroup.create(process.pid)
        return self

    async def __aexit__(self, *args) -> None:
        if self.cgroups_task:
            self.cgroups_task.cancel()

        if self.process_end is not None:
            if not self.is_running():
                await self.process_end
                raise AssertionError(f"{self.name} died without being waited for or killed")
            await self.kill()
