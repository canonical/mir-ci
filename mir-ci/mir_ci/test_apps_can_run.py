from mir_ci.display_server import DisplayServer
import pytest
import time

from mir_ci import apps
from mir_ci.benchmarker import Benchmarker

short_wait_time = 3

class TestAppsCanRun:
    @pytest.mark.smoke
    @pytest.mark.parametrize('app', [
        apps.wpe(),
        apps.snap('mir-kiosk-neverputt'),
        apps.snap('mir-kiosk-scummvm'),
        apps.snap('mir-kiosk-kodi'),
        apps.pluma(),
        apps.qterminal(),
    ])
    async def test_app_can_run(self, server, app, record_property) -> None:
        benchmarker = Benchmarker(poll_time_seconds=0.1)
        def on_program_started(pid: int, name: str):
            benchmarker.add(pid, name)
            
        async with DisplayServer(server, on_program_started=on_program_started) as server:
            async with server.program(app) as p:
                async with benchmarker:
                    time.sleep(short_wait_time)
                    await p.kill(2)

        benchmarker.generate_report(record_property)
