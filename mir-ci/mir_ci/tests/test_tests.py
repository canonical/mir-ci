import asyncio
import os
import random
import time
from collections import OrderedDict
from contextlib import suppress
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, Mock, call, mock_open, patch

import pytest
from mir_ci.fixtures.servers import ServerCap, _mir_ci_server, servers
from mir_ci.lib.benchmarker import Benchmarker, CgroupsBackend
from mir_ci.lib.cgroups import Cgroup
from mir_ci.program.app import App, AppType
from mir_ci.program.display_server import DisplayServer
from mir_ci.program.program import Program
from mir_ci.wayland.output_watcher import OutputWatcher
from mir_ci.wayland.protocols import WlOutput


def _async_return(mock=None):
    f = asyncio.Future()
    f.set_result(mock or MagicMock())
    return f


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
        p = Program(App(["sh", "-c", "sleep 1"], AppType.deb))
        async with p:
            await asyncio.sleep(0.5)
            await p.kill(2)
        mock_uuid.assert_called_once()

    async def test_program_can_get_cgroup(self) -> None:
        p = Program(App(["sh", "-c", "sleep 100"], AppType.deb))
        async with p:
            cgroup = await p.get_cgroup()
            assert cgroup is not None
            await p.kill(2)

    @patch("mir_ci.program.program.Path")
    @patch("mir_ci.lib.cgroups.Cgroup.create")
    async def test_passes_when_cgroup_not_got(self, mock_create, mock_path) -> None:
        mock_path.return_value.exists.return_value = False
        mock_create.side_effect = FileNotFoundError

        p = Program(App(["sh", "-c", "sleep 100"], AppType.deb))
        async with p:
            await p.kill(2)

    @patch("mir_ci.program.program.Path")
    async def test_get_cgroup_asserts_without_cgroupv2(self, mock_path) -> None:
        mock_path.return_value.exists.return_value = False

        p = Program(App(["sh", "-c", "sleep 100"], AppType.deb))
        with pytest.raises(AssertionError, match="Cgroup task is None, is cgroupv2 supported?"):
            async with p:
                await p.get_cgroup()


@pytest.mark.self
class TestBenchmarker(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.parent_mock = Mock()
        return super().setUp()

    def create_program_mock(self, name="mock"):
        p = MagicMock()
        p.get_cgroup = Mock(return_value=_async_return())
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

    async def test_benchmarker_unwinds_programs_on_task_failure(self) -> None:
        p1 = self.create_program_mock("p1")

        benchmarker = Benchmarker({"p1": p1})

        with pytest.raises(Exception, match="cancel exception"):
            async with benchmarker:
                # FIXME: this reaches too deep into Benchmarker
                if benchmarker.task is not None:
                    benchmarker.task.cancel()
                    with suppress(asyncio.CancelledError):
                        await benchmarker.task
                benchmarker.task = Mock()
                benchmarker.task.cancel.side_effect = Exception("cancel exception")

        call.p1.__aexit__.assert_called_once()


@pytest.mark.self
class TestCGroupsBackend:
    async def test_eats_runtime_error_on_poll(self):
        pi = Mock()
        pi.get_cgroup.side_effect = RuntimeError("read error")

        cgb = CgroupsBackend()
        cgb.add("pi", pi)

        with pytest.raises(UserWarning, match="Ignoring cgroup read failure: read error"):
            await cgb.poll()

    @pytest.mark.filterwarnings("error")
    async def test_converts_max_to_peak(self):
        pi = Mock()
        cg = Mock()
        pi.get_cgroup.return_value = _async_return(cg)
        cg.get_current_memory.return_value = random.randint(0, 100)
        cg.get_peak_memory.side_effect = RuntimeError

        cgb = CgroupsBackend()
        cgb.add("pi", pi)

        await cgb.poll()

        assert cgb.generate_report() == {
            "pi_cpu_time_microseconds": cg.get_cpu_time_microseconds.return_value,
            "pi_max_mem_bytes": cg.get_current_memory.return_value,
            "pi_avg_mem_bytes": cg.get_current_memory.return_value,
        }

    @pytest.mark.filterwarnings("ignore:Ignoring cgroup")
    async def test_raises_runtime_error_on_empty(self):
        pi = Mock()
        pi.get_cgroup.side_effect = RuntimeError("read error")

        cgb = CgroupsBackend()
        cgb.add("pi", pi)

        await cgb.poll()

        with pytest.raises(RuntimeError, match="Failed to collect benchmarking data"):
            cgb.generate_report()


@pytest.mark.self
class TestCgroup:
    @patch(
        "builtins.open", new_callable=mock_open, read_data="usage_usec 100\nline_two 30\nline_three 40\nline_four 50"
    )
    def test_cgroup_can_get_cpu_time_microseconds(self, mock_open):
        cgroup = Cgroup("/fake/path")
        assert cgroup.get_cpu_time_microseconds() == 100

    @patch("builtins.open", new_callable=mock_open, read_data="usage_usec string")
    def test_cgroup_get_cpu_time_microseconds_raises_when_not_integer(self, mock_open):
        cgroup = Cgroup("/fake/path")
        with pytest.raises(RuntimeError, match="Unable to get the cpu time for cgroup: /fake/path"):
            cgroup.get_cpu_time_microseconds()

    @patch("builtins.open", new_callable=mock_open, read_data="100")
    def test_cgroup_get_cpu_time_microseconds_raises_when_usage_usec_not_found(self, mock_open):
        cgroup = Cgroup("/fake/path")
        with pytest.raises(RuntimeError, match="Unable to get the cpu time for cgroup: /fake/path"):
            cgroup.get_cpu_time_microseconds()

    @patch("builtins.open", new_callable=mock_open, read_data="100")
    def test_cgroup_can_get_current_memory(self, mock_open):
        cgroup = Cgroup("/fake/path")
        assert cgroup.get_current_memory() == 100

    @patch("builtins.open", new_callable=mock_open, read_data="string")
    def test_cgroup_get_current_memory_raises_when_not_integer(self, mock_open):
        cgroup = Cgroup("/fake/path")
        with pytest.raises(RuntimeError, match="Unable to get the current memory for cgroup: /fake/path"):
            cgroup.get_current_memory()

    @patch("builtins.open", new_callable=mock_open, read_data="100")
    def test_cgroup_can_get_peak_memory(self, mock_open):
        cgroup = Cgroup("/fake/path")
        assert cgroup.get_peak_memory() == 100

    @patch("builtins.open", new_callable=mock_open, read_data="string")
    def test_cgroup_get_peak_memory_raises_when_not_integer(self, mock_open):
        cgroup = Cgroup("/fake/path")
        with pytest.raises(RuntimeError, match="Unable to get the peak memory for cgroup: /fake/path"):
            cgroup.get_peak_memory()

    @patch("builtins.open", new_callable=mock_open, read_data="string")
    async def test_cgroup_path_raises_assertion_error_when_contents_are_incorrect(self, mock_open):
        with pytest.raises(AssertionError, match=f"Line in cgroup file does not start with 0:: for pid: {os.getpid()}"):
            await Cgroup.get_cgroup_dir(12345)

    @patch("builtins.open", new_callable=mock_open)
    async def test_cgroup_path_raises_runtime_error_when_contents_are_none(self, mock_open):
        with pytest.raises(RuntimeError, match=f"Unable to find path for process with pid: {os.getpid()}"):
            await Cgroup.get_cgroup_dir(12345)

    @patch("builtins.open", new_callable=mock_open, read_data="0::path")
    async def test_group_path_warns_when_no_child_found(self, mock_open):
        with pytest.warns(UserWarning, match="Unable to find child cgroup"):
            assert await Cgroup.get_cgroup_dir(12345) == Path("/sys/fs/cgroup/path")


@pytest.mark.self
class TestDisplayServer:
    async def test_can_get_cgroup(self, any_server):
        server_instance = DisplayServer(any_server)
        async with server_instance:
            cgroup = await server_instance.get_cgroup()
            assert cgroup is not None

    def test_display_server_records_mode(self) -> None:
        mock_fixture = Mock()
        server = DisplayServer(App("foo"))

        class MockServer:
            output = """Current mode 123x456 78.9Hz
                        GL renderer: Mock renderer"""

        with patch.object(server, "server", MockServer()):
            server.record_properties(mock_fixture)

        mock_fixture.assert_has_calls([call("server_mode", "123x456 78.9Hz"), call("server_renderer", "Mock renderer")])


@pytest.mark.self
class TestOutputWatcher:
    def test_can_register(self) -> None:
        mock_fixture = MagicMock()
        watcher = OutputWatcher("test-display-name")
        watcher.registry_global(mock_fixture, 12345, WlOutput.name, 1)
        mock_fixture.assert_has_calls(
            [
                call.bind(12345, WlOutput, 1),
                call.bind().dispatcher.__setitem__("geometry", None),
                call.bind().dispatcher.__setitem__("mode", None),
                call.bind().dispatcher.__setitem__("scale", None),
                call.bind().dispatcher.__setitem__("name", None),
            ]
        )


@pytest.mark.self
class TestServers:
    def is_server(self, server, app_type: AppType):
        return server[2] == f"my-pretend-{app_type.name}"

    @pytest.mark.parametrize("app_type", [AppType.snap, AppType.deb, AppType.pip])
    def test_can_parse_mir_ci_server(self, monkeypatch, app_type: AppType) -> None:
        monkeypatch.setenv("MIR_CI_SERVER", f"{app_type.name}:my-pretend-{app_type.name}:ALL")
        server = _mir_ci_server()
        app = server[1]()[0][0]
        assert server is not None
        if app_type == AppType.pip:
            assert app.command == ("python3", "-m", f"my-pretend-{app_type.name}")
        else:
            assert app.command == (f"my-pretend-{app_type.name}",)
        assert app.app_type == app_type

    @pytest.mark.parametrize("app_type", [AppType.snap, AppType.deb, AppType.pip])
    def test_mir_ci_server_string_missing_capabilities(self, monkeypatch, app_type: AppType) -> None:
        with pytest.raises(UserWarning):
            monkeypatch.setenv("MIR_CI_SERVER", f"{app_type.name}:my-pretend-{app_type.name}")
            _mir_ci_server()

    def test_mir_ci_server_string_app_type_is_invalid(self, monkeypatch) -> None:
        with pytest.raises(UserWarning):
            monkeypatch.setenv("MIR_CI_SERVER", "invalid:my-pretend-invalid:ALL")
            _mir_ci_server()

    @pytest.mark.parametrize("app_type", [AppType.snap, AppType.deb, AppType.pip])
    def test_mir_ci_server_string_capability_is_invalid(self, monkeypatch, app_type: AppType) -> None:
        with pytest.raises(UserWarning):
            monkeypatch.setenv("MIR_CI_SERVER", f"{app_type.name}:my-pretend-{app_type.name}:INVALID")
            _mir_ci_server()

    @pytest.mark.parametrize("app_type", [AppType.snap, AppType.deb, AppType.pip])
    def test_mir_ci_server_is_present_in_server_list(self, monkeypatch, app_type: AppType) -> None:
        monkeypatch.setenv("MIR_CI_SERVER", f"{app_type.name}:my-pretend-{app_type.name}:ALL")
        matches = next((server for server in servers() if self.is_server(server, app_type)), None)
        assert matches is not None

    @pytest.mark.parametrize("app_type", [AppType.snap, AppType.deb, AppType.pip])
    @pytest.mark.parametrize(
        "capabilities",
        [
            [ServerCap.FLOATING_WINDOWS.name, ServerCap.DRAG_AND_DROP.name],
            [ServerCap.SCREENCOPY.name, ServerCap.INPUT_METHOD.name],
            [ServerCap.DISPLAY_CONFIG.name],
        ],
    )
    def test_mir_ci_server_can_be_found_by_capability(self, monkeypatch, app_type, capabilities: list[str]) -> None:
        monkeypatch.setenv("MIR_CI_SERVER", f"{app_type.name}:my-pretend-{app_type.name}:{':'.join(capabilities)}")
        capability = ServerCap.NONE
        for capability_str in capabilities:
            capability = capability & ServerCap[capability_str]

        matches = next((server for server in servers(capability) if self.is_server(server, app_type)), None)
        assert matches is not None

    @pytest.mark.parametrize("app_type", [AppType.snap, AppType.deb, AppType.pip])
    def test_mir_ci_server_cannot_be_found_if_it_lacks_capability(self, monkeypatch, app_type) -> None:
        monkeypatch.setenv("MIR_CI_SERVER", f"{app_type.name}:my-pretend-{app_type.name}:FLOATING_WINDOWS:SCREENCOPY")
        matches = next(
            (server for server in servers(ServerCap.DISPLAY_CONFIG) if self.is_server(server, app_type)), None
        )
        assert matches is None
