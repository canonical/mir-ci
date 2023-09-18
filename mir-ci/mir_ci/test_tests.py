import os
import subprocess
import time
import pytest
import asyncio
import subprocess
import time

from mir_ci.program import Program
from mir_ci.benchmarker import Benchmarker
from mir_ci.cgroups import Cgroup

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

    def test_program_command_has_prefix_when_systemd_slice_is_set(self) -> None:
        p = Program(['sh', '-c', 'sleep 1; echo abc'], systemd_slice="test-slice")
        assert p.command == ("systemd-run", "--user", "--scope", "--slice=test-slice", "sh", "-c", "sleep 1; echo abc")

    async def test_program_has_cgroup_file_when_run_with_slice(self) -> None:
        p = Program(['sh', '-c', 'sleep 1; echo abc'], systemd_slice="test-slice")
        async with p:
            await asyncio.sleep(1)
            if p.process:
                cgroup_dir = Cgroup.get_cgroup_dir(p.process.pid)
                assert cgroup_dir is not None
                assert str(cgroup_dir).find("test-slice")
                await p.kill(2)


class TestBenchmarker:
    async def test_benchmarker_with_popen(self) -> None:
        benchmarker = Benchmarker(poll_time_seconds=0.1)
        p = subprocess.Popen(['sh', '-c', 'sleep 1;'])

        if p is not None:
            benchmarker.add(p.pid, "sleep")
        async with benchmarker:
            await asyncio.sleep(1)

        assert len(benchmarker.get_data()) > 0
        assert benchmarker.get_data()[0].pid == p.pid

    async def test_benchmarker_with_program(self) -> None:
        benchmarker = Benchmarker(poll_time_seconds=0.1)
        p = Program(['sh', '-c', 'sleep 1;'])
        async with p:
            if p.process is not None:
                benchmarker.add(p.process.pid, "sleep")
            async with benchmarker:
                await asyncio.sleep(1)
                await p.kill(2)

        assert len(benchmarker.get_data()) > 0
        assert p.process is not None
        if p.process is not None:
            assert benchmarker.get_data()[0].pid == p.process.pid

    async def test_benchmarker_cpu_has_value(self) -> None:
        benchmarker = Benchmarker(poll_time_seconds=0.1)
        p = Program(['awk', 'BEGIN{for(i=0;i<100000000;i++){}}'])
        async with p:
            if p.process is not None:
                benchmarker.add(p.process.pid, "awk")
            async with benchmarker:
                await asyncio.sleep(1)

        assert len(benchmarker.get_data()) > 0
        assert benchmarker.get_data()[0].max_mem_bytes > 0
        assert benchmarker.get_data()[0].avg_cpu_percent > 0

    async def test_benchmarker_can_measure_snaps(self) -> None:
        benchmarker = Benchmarker(poll_time_seconds=0.1)
        p = Program(
            "ubuntu-frame",
            env={
                'WAYLAND_DISPLAY': "wayland-99"
            })

        async with p:
            if p.process is not None:
                benchmarker.add(p.process.pid, "frame")
                async with benchmarker:
                    await asyncio.sleep(3)
                    await p.kill(2)
                    
        assert len(benchmarker.get_data()) > 0
        assert benchmarker.get_data()[0].max_mem_bytes > 0
        assert benchmarker.get_data()[0].avg_cpu_percent > 0
