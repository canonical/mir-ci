from mir_ci import SLOWDOWN
from mir_ci.display_server import DisplayServer
import pytest
import asyncio

from mir_ci import apps
from mir_ci.benchmarker import Benchmarker

short_wait_time = 3 * SLOWDOWN


class TestAppsCanRun:
    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "app",
        [
            apps.wpe(),
            apps.snap("mir-kiosk-neverputt"),
            apps.snap("mir-kiosk-scummvm"),
            apps.snap("mir-kiosk-kodi"),
            apps.pluma(),
            apps.qterminal(),
        ],
    )
    async def test_app_can_run(self, server, app, record_property) -> None:
        server_instance = DisplayServer(server)
        program = server_instance.program(app)
        benchmarker = Benchmarker({"compositor": server_instance, "client": program}, poll_time_seconds=0.1)
        async with benchmarker:
            await asyncio.sleep(short_wait_time)

        benchmarker.generate_report(record_property)
