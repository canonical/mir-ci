import asyncio
from unittest.mock import ANY, Mock

import pytest
from display_server_static_file import DisplayServerStaticFile
from mir_ci import SLOWDOWN
from mir_ci.fixtures.servers import ServerCap, servers
from mir_ci.wayland.output_watcher import OutputWatcher

short_wait_time = 1 * SLOWDOWN


# TODO: Test other servers. Frame-based servers use
# a configuration file that is within the snap, so it
# is unclear how to read/modify that file from the outside
@pytest.mark.parametrize("server", servers(ServerCap.DISPLAY_CONFIG))
@pytest.mark.deps(pip_pkgs=("pyyaml",))
class TestDisplayConfiguration:
    async def test_can_update_scale(self, server) -> None:
        server = DisplayServerStaticFile(server)
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
        server = DisplayServerStaticFile(server)
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
