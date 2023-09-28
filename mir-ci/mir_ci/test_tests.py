import asyncio
import os
import time
from collections import OrderedDict
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, Mock, call, mock_open, patch

import pytest
from mir_ci.apps import App
from mir_ci.benchmarker import Benchmarker
from mir_ci.cgroups import Cgroup
from mir_ci.display_server import DisplayServer
from mir_ci.program import Program


@pytest.mark.self
class TestProgram:
    async def test_program_gives_output(self) -> None:
        p = Program(App(["printf", "%s - %s", "abc", "xyz"]))
        async with p:
            await p.wait()
        assert p.output == "abc - xyz"

    async def test_program_can_be_waited_for(self) -> None:
        start = time.time()
        p = Program(App(["sh", "-c", "sleep 1; echo abc"]))
        async with p:
            await p.wait()
        elapsed = time.time() - start
        assert p.output.strip() == "abc"
        assert abs(elapsed - 1) < 0.1

    async def test_program_can_be_terminated(self) -> None:
        start = time.time()
        p = Program(App(["sh", "-c", "echo abc; sleep 1; echo ijk"]))
        async with p:
            await asyncio.sleep(0.5)
            await p.kill(2)
        elapsed = time.time() - start
        assert p.output.strip() == "abc"
        assert abs(elapsed - 0.5) < 0.1

    async def test_program_is_killed_when_terminate_fails(self) -> None:
        start = time.time()
        p = Program(App(["sh", "-c", 'trap "" TERM; echo abc; sleep 1; echo ijk; sleep 5; echo xyz']))
        async with p:
            await asyncio.sleep(0.5)
            await p.kill(2)
        elapsed = time.time() - start
        assert p.output.strip() == "abc\nijk"
        assert abs(elapsed - 2.5) < 0.1

    @patch("uuid.uuid4")
    async def test_program_runs_with_systemd_when_flag_is_set(self, mock_uuid) -> None:
        mock_uuid.return_value = "12345"
        p = Program(App(["sh", "-c", "sleep 1"], "deb"))
        async with p:
            await asyncio.sleep(0.5)
            await p.kill(2)
        mock_uuid.assert_called_once()

    async def test_program_can_get_cgroup(self) -> None:
        p = Program(App(["sh", "-c", "sleep 100"], "deb"))
        async with p:
            cgroup = await p.get_cgroup()
            assert cgroup is not None
            await p.kill(2)


@pytest.mark.self
class TestBenchmarker(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.parent_mock = Mock()
        return super().setUp()

    def create_program_mock(self, name="mock"):
        def async_return():
            f = asyncio.Future()
            f.set_result(MagicMock())
            return f

        p = MagicMock()
        p.get_cgroup = Mock(return_value=async_return())
        self.parent_mock.attach_mock(p, name)
        return p

    async def test_benchmarker_with_program(self) -> None:
        p = self.create_program_mock()
        benchmarker = Benchmarker({"program": p}, poll_time_seconds=0.1)
        async with benchmarker:
            await asyncio.sleep(1)

        p.get_cgroup.assert_called()
        p.__aenter__.assert_called_once()
        p.__aexit__.assert_called_once()

    async def test_benchmarker_can_generate_report(self) -> None:
        p = self.create_program_mock()
        benchmarker = Benchmarker({"program": p}, poll_time_seconds=0.1)
        async with benchmarker:
            await asyncio.sleep(1)

        callback = Mock()
        benchmarker.generate_report(callback)
        callback.assert_called()

    async def test_benchmarker_cant_enter_twice(self) -> None:
        p = self.create_program_mock()
        benchmarker = Benchmarker({"program": p}, poll_time_seconds=0.1)
        async with benchmarker:
            async with benchmarker:
                await asyncio.sleep(1)

        p.__aenter__.assert_called_once()

    async def test_benchmarker_unwinds_programs(self) -> None:
        p1 = self.create_program_mock("p1")
        p2 = self.create_program_mock("p2")
        benchmarker = Benchmarker(OrderedDict(p1=p1, p2=p2), poll_time_seconds=0.1)
        async with benchmarker:
            pass

        assert self.parent_mock.mock_calls[:2] == [
            call.p1.__aenter__(),
            call.p2.__aenter__(),
        ]

        assert self.parent_mock.mock_calls[-2:] == [
            call.p2.__aexit__(),
            call.p1.__aexit__(),
        ]

    async def test_benchmarker_unwinds_programs_on_enter_failure(self) -> None:
        p1 = self.create_program_mock("p1")
        p2 = self.create_program_mock("p2")
        p3 = self.create_program_mock("p3")
        p2.__aenter__.side_effect = Exception("enter exception")

        benchmarker = Benchmarker(OrderedDict(p1=p1, p2=p2, p3=p3))

        with pytest.raises(Exception, match="enter exception"):
            async with benchmarker:
                pass

        self.parent_mock.assert_has_calls(
            [
                call.p1.__aenter__(),
                call.p2.__aenter__(),
                call.p1.__aexit__(),
            ]
        )

    async def test_benchmarker_unwinds_programs_on_exit_failure(self) -> None:
        p1 = self.create_program_mock("p1")
        p2 = self.create_program_mock("p2")
        p3 = self.create_program_mock("p3")
        p2.__aexit__.side_effect = Exception("exit exception")

        benchmarker = Benchmarker(OrderedDict(p1=p1, p2=p2, p3=p3))

        with pytest.raises(Exception, match="exit exception"):
            async with benchmarker:
                pass

        assert self.parent_mock.mock_calls[-3:] == [
            call.p3.__aexit__(),
            call.p2.__aexit__(),
            call.p1.__aexit__(),
        ]


@pytest.mark.self
class TestCgroup:
    @patch(
        "builtins.open", new_callable=mock_open, read_data="usage_usec 100\nline_two 30\nline_three 40\nline_four 50"
    )
    def test_cgroup_can_get_cpu_time_microseconds(self, mock_open):
        cgroup = Cgroup(12345, "/fake/path")
        assert cgroup.get_cpu_time_microseconds() == 100

    @patch("builtins.open", new_callable=mock_open, read_data="usage_usec string")
    def test_cgroup_get_cpu_time_microseconds_raises_when_not_integer(self, mock_open):
        cgroup = Cgroup(12345, "/fake/path")
        with pytest.raises(RuntimeError, match="Unable to get the cpu time for cgroup with pid: 12345"):
            cgroup.get_cpu_time_microseconds()

    @patch("builtins.open", new_callable=mock_open, read_data="100")
    def test_cgroup_get_cpu_time_microseconds_raises_when_usage_usec_not_found(self, mock_open):
        cgroup = Cgroup(12345, "/fake/path")
        with pytest.raises(RuntimeError, match="Unable to get the cpu time for cgroup with pid: 12345"):
            cgroup.get_cpu_time_microseconds()

    @patch("builtins.open", new_callable=mock_open, read_data="100")
    def test_cgroup_can_get_current_memory(self, mock_open):
        cgroup = Cgroup(12345, "/fake/path")
        assert cgroup.get_current_memory() == 100

    @patch("builtins.open", new_callable=mock_open, read_data="string")
    def test_cgroup_get_current_memory_raises_when_not_integer(self, mock_open):
        cgroup = Cgroup(12345, "/fake/path")
        with pytest.raises(RuntimeError, match="Unable to get the current memory for cgroup with pid: 12345"):
            cgroup.get_current_memory()

    @patch("builtins.open", new_callable=mock_open, read_data="100")
    def test_cgroup_can_get_peak_memory(self, mock_open):
        cgroup = Cgroup(12345, "/fake/path")
        assert cgroup.get_peak_memory() == 100

    @patch("builtins.open", new_callable=mock_open, read_data="string")
    def test_cgroup_get_peak_memory_raises_when_not_integer(self, mock_open):
        cgroup = Cgroup(12345, "/fake/path")
        with pytest.raises(RuntimeError, match="Unable to get the peak memory for cgroup with pid: 12345"):
            cgroup.get_peak_memory()

    @patch("builtins.open", new_callable=mock_open, read_data="string")
    async def test_cgroup_path_raises_assertion_error_when_contents_are_incorrect(self, mock_open):
        with pytest.raises(AssertionError, match=f"Line in cgroup file does not start with 0:: for pid: {os.getpid()}"):
            await Cgroup.get_cgroup_dir(12345)

    @patch("builtins.open", new_callable=mock_open)
    async def test_cgroup_path_raises_runtime_error_when_contents_are_none(self, mock_open):
        with pytest.raises(RuntimeError, match=f"Unable to find path for process with pid: {os.getpid()}"):
            await Cgroup.get_cgroup_dir(12345)


@pytest.mark.self
class TestDisplayServer:
    async def test_can_get_cgroup(self, server):
        server_instance = DisplayServer(server)
        async with server_instance:
            cgroup = await server_instance.get_cgroup()
            assert cgroup is not None
