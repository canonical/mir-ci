import asyncio
import importlib
import os
import tempfile
from typing import Any
from unittest.mock import ANY, Mock

import pytest
from mir_ci import SLOWDOWN, apps
from mir_ci.display_server import DisplayServer
from mir_ci.output_watcher import OutputWatcher

short_wait_time = 1 * SLOWDOWN


class DisplayServerStaticFile:
    def __init__(self, local_server):
        self.local_server = local_server
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        self.tmp_filename = tmp_file.name
        try:
            os.remove(self.tmp_filename)
        except OSError:
            pass

        self.server = DisplayServer(self.local_server, env={"MIR_SERVER_DISPLAY_CONFIG": f"static={self.tmp_filename}"})

    async def __aenter__(self) -> "DisplayServerStaticFile":
        await self.server.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self.server.__aexit__(*args)

    def read_config(self) -> Any:
        yaml = importlib.import_module("yaml")
        with open(self.tmp_filename, "r") as file:
            # the yaml parser doesn't like tabs before our comments
            content = file.read().replace("\t#", "  #")
            data = yaml.safe_load(content)
            return data

    def write_config(self, content: Any) -> None:
        yaml = importlib.import_module("yaml")
        with open(self.tmp_filename, "w") as file:
            yaml.dump(content, file)


@pytest.mark.parametrize(
    "local_server",
    [
        # TODO: Test other servers. Frame-based servers use
        # a configuration file that is within the snap, so it
        # is unclear how to read/modify that file from the outside
        apps.mir_demo_server(),
    ],
)
class TestDisplayConfiguration:
    @pytest.mark.deps(pip_pkgs=("pyyaml",))
    async def test_can_update_scale(self, local_server) -> None:
        server = DisplayServerStaticFile(local_server)
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

    @pytest.mark.deps(pip_pkgs=("pyyaml",))
    async def test_can_update_position(self, local_server) -> None:
        server = DisplayServerStaticFile(local_server)
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
