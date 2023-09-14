from mir_ci.display_server import DisplayServer
import pytest
import time

from mir_ci import apps

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
    async def test_app_can_run(self, server, app, record_property: pytest.FixtureRequest) -> None:
        async with DisplayServer(server, benchmark=True) as server:
            async with server.program(app):
                time.sleep(short_wait_time)

            server.generate_report(record_property)
