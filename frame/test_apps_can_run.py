from display_server import DisplayServer
import pytest
from benchmarker import benchmarker, Benchmarker
import asyncio

import apps

short_wait_time = 10

class TestAppsCanRun:
    @pytest.mark.smoke
    @pytest.mark.parametrize('app', [
        apps.wpe(),
    ])

    async def test_app_can_run(self, server, app, benchmarker: Benchmarker, record_property) -> None:
        async with benchmarker:
            async with DisplayServer(server) as server:
                async with server.program(app) as program:
                    benchmarker.add(server.server.process.pid, "Compositor")
                    benchmarker.add(program.process.pid, "Application")
                    await asyncio.sleep(short_wait_time)

        await benchmarker.stop()
        record_property(app[0], benchmarker.get_data())
