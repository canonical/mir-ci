import asyncio
from unittest.mock import ANY, Mock

import pytest
from mir_ci import SLOWDOWN
from mir_ci.fixtures.servers import ServerCap, servers
from mir_ci.program.display_server import DisplayServerWithDisplayConfig
from mir_ci.wayland.output_watcher import OutputWatcher

short_wait_time = 1 * SLOWDOWN


@pytest.mark.parametrize("server", servers(ServerCap.DISPLAY_CONFIG))
class TestDisplayConfiguration:
    async def test_can_update_scale(self, server) -> None:
        server = DisplayServerWithDisplayConfig(server)
        on_scale = Mock()
        watcher = OutputWatcher(server.server.display_name, on_scale=on_scale)

        async with server, watcher:
            await asyncio.sleep(short_wait_time)
            data = server.read_config()

            card = data["layouts"]["default"]["cards"][0]
            for v in card.values():
                if type(v) is dict:
                    v["scale"] = 2
                    break

            server.write_config(data)
            await asyncio.sleep(short_wait_time)

        on_scale.assert_called_with(ANY, 2)

    async def test_can_update_position(self, server) -> None:
        server = DisplayServerWithDisplayConfig(server)
        on_geometry = Mock()
        watcher = OutputWatcher(server.server.display_name, on_geometry=on_geometry)

        async with server, watcher:
            await asyncio.sleep(short_wait_time)
            data = server.read_config()

            card = data["layouts"]["default"]["cards"][0]
            for v in card.values():
                if type(v) is dict:
                    v["position"] = [10, 20]
                    break

            server.write_config(data)
            await asyncio.sleep(short_wait_time)

        on_geometry.assert_called_with(ANY, 10, 20, ANY, ANY, ANY, ANY, ANY, ANY)
