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
    async def test_app_can_run(self, server, app: apps.Dependency, record_property) -> None:
        benchmarker = Benchmarker(poll_time_seconds=0.1)
        async with DisplayServer(server) as server:
            async with server.program(app.command, app_type=app.app_type) as p:
                if server.server is not None and server.server.process is not None:
                    benchmarker.add(server.server.process.pid, "compositor")
                if p.process is not None:
                    benchmarker.add(p.process.pid, "application")
                    
                async with benchmarker:
                    time.sleep(short_wait_time)
                    await p.kill(2)

        benchmarker.generate_report(record_property)
