import os
import subprocess
import time
import pytest
import asyncio
import subprocess

from mir_ci.program import Program
from mir_ci.benchmarker import Benchmarker, benchmarker_preexec_fn

class TestTest:
    @pytest.mark.self
    @pytest.mark.deps('python3', '-m', 'mypy', pip_pkgs=('mypy', 'pywayland'))
    def test_project_typechecks(self, deps) -> None:
        from mir_ci.protocols import WlOutput, WlShm, ZwlrScreencopyManagerV1  # noqa:F401
        project_path = os.path.dirname(__file__)
        assert os.path.isfile(os.path.join(project_path, 'pytest.ini')), 'project path not detected correctly'
        result = subprocess.run(
            [*deps, project_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True)
        if result.returncode != 0:
            raise RuntimeError('`$ mypy ' + project_path + '` failed:\n\n' + result.stdout)

@pytest.mark.self
class TestProgram:
    async def test_program_gives_output(self) -> None:
        p = Program(['printf', '%s - %s', 'abc', 'xyz'])
        async with p:
            await p.wait()
        assert p.output == 'abc - xyz'

    async def test_program_can_be_waited_for(self) -> None:
        start = time.time()
        p = Program(['sh', '-c', 'sleep 1; echo abc'])
        async with p:
            await p.wait()
        elapsed = time.time() - start
        assert p.output.strip() == 'abc'
        assert abs(elapsed - 1) < 0.1

    async def test_program_can_be_terminated(self) -> None:
        start = time.time()
        p = Program(['sh', '-c', 'echo abc; sleep 1; echo ijk'])
        async with p:
            await asyncio.sleep(0.5)
            await p.kill(2)
        elapsed = time.time() - start
        assert p.output.strip() == 'abc'
        assert abs(elapsed - 0.5) < 0.1

    async def test_program_is_killed_when_terminate_fails(self) -> None:
        start = time.time()
        p = Program(['sh', '-c', 'trap "" TERM; echo abc; sleep 1; echo ijk; sleep 5; echo xyz'])
        async with p:
            await asyncio.sleep(0.5)
            await p.kill(2)
        elapsed = time.time() - start
        assert p.output.strip() == 'abc\nijk'
        assert abs(elapsed - 2.5) < 0.1


class TestBenchmarker:
    @staticmethod
    def add_to_benchmark():
        # WARNING: This happens in a forked process. We do not
        # have access to memory from the parent process here.
        benchmarker_preexec_fn("sleepy")

    async def test_benchmarker_with_popen(self) -> None:
        benchmarker = Benchmarker(poll_time_seconds=0.1, backend="psutil")
        p = subprocess.Popen(['sh', '-c', 'sleep 1;'], preexec_fn=TestBenchmarker.add_to_benchmark)
        async with benchmarker:
            await asyncio.sleep(1)

        assert len(benchmarker.get_data()) > 0
        assert benchmarker.get_data()[0].pid == p.pid

    async def test_benchmarker_with_program(self) -> None:
        benchmarker = Benchmarker(poll_time_seconds=0.1, backend="psutil")
        p = Program(['sh', '-c', 'sleep 1;'], preexec_fn=TestBenchmarker.add_to_benchmark)
        async with p:
            async with benchmarker:
                await asyncio.sleep(1)
                await p.kill(2)

        assert len(benchmarker.get_data()) > 0
        assert benchmarker.get_data()[0].pid == p.process.pid

    async def test_benchmarker_cpu_has_value(self) -> None:
        benchmarker = Benchmarker(poll_time_seconds=0.1, backend="psutil")
        p = Program(['awk', 'BEGIN{for(i=0;i<100000000;i++){}}'], preexec_fn=TestBenchmarker.add_to_benchmark)
        async with p:
            async with benchmarker:
                await asyncio.sleep(3)
                await p.kill(2)

        assert len(benchmarker.get_data()) > 0
        assert benchmarker.get_data()[0].max_mem_bytes > 0
        assert benchmarker.get_data()[0].avg_cpu_percent > 0
