import asyncio
from collections import OrderedDict

import pytest
from mir_ci import SLOWDOWN
from mir_ci.fixtures import apps
from mir_ci.lib.benchmarker import Benchmarker
from mir_ci.program.display_server import DisplayServer

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
    async def test_app_can_run(self, mir_and_nonmir_server, app, record_property) -> None:
        server_instance = DisplayServer(mir_and_nonmir_server)
        program = server_instance.program(app)
        benchmarker = Benchmarker(OrderedDict(compositor=server_instance, client=program), poll_time_seconds=0.1)
        async with benchmarker:
            await asyncio.sleep(short_wait_time)

        server_instance.record_properties(record_property)
        benchmarker.generate_report(record_property)
