from unittest.mock import ANY, Mock

import pytest
from mir_ci import SLOWDOWN
from mir_ci.fixtures.servers import ServerCap, servers
from mir_ci.lib import await_call
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
            await await_call(on_scale, ANY, ANY)
            data = server.read_config()

            card = data["layouts"]["default"]["cards"][0]
            for v in card.values():
                if type(v) is dict:
                    v["scale"] = 2
                    # FIXME: overlapping displays of different scale cause Mir to crash
                    # https://github.com/canonical/mir/issues/3888
                    # break

            server.write_config(data)
            await await_call(on_scale, ANY, 2)

    async def test_can_update_position(self, server) -> None:
        server = DisplayServerWithDisplayConfig(server)
        on_geometry = Mock()
        watcher = OutputWatcher(server.server.display_name, on_geometry=on_geometry)

        async with server, watcher:
            await await_call(on_geometry, ANY, ANY, ANY, ANY, ANY, ANY, ANY, ANY, ANY)
            data = server.read_config()

            card = data["layouts"]["default"]["cards"][0]
            for v in card.values():
                if type(v) is dict:
                    v["position"] = [10, 20]
                    break

            server.write_config(data)
            await await_call(on_geometry, ANY, 10, 20, ANY, ANY, ANY, ANY, ANY, ANY)
