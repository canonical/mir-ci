import os
import subprocess
import time
import pytest
import asyncio

from program import Program

class TestTest:
    @pytest.mark.self
    @pytest.mark.deps('python3', '-m', 'mypy', pip_pkgs=('mypy',))
    def test_project_typechecks(self, deps) -> None:
        project_path = os.path.dirname(__file__)
        assert os.path.isfile(os.path.join(project_path, 'requirements.txt')), 'project path not detected correctly'
        result = subprocess.run(
            [*deps, project_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True)
        if result.returncode != 0:
            raise RuntimeError('`$ mypy ' + project_path + '` failed:\n\n' + result.stdout)

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
