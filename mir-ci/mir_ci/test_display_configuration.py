import asyncio
import importlib
import os
from unittest.mock import ANY, Mock

import pytest
from mir_ci import SLOWDOWN, apps
from mir_ci.display_server import DisplayServer
from mir_ci.output_watcher import OutputWatcher

short_wait_time = 1 * SLOWDOWN


class TestDisplayConfiguration:
    @pytest.mark.parametrize(
        "local_server",
        [
            apps.mir_demo_server(),
        ],
    )
    @pytest.mark.deps(pip_pkgs=("pyyaml",))
    async def test_can_update_scale(self, local_server) -> None:
        CONFIG_FILE = "/tmp/mir_ci_display_config.yaml"
        try:
            os.remove(CONFIG_FILE)
        except OSError:
            pass

        server = DisplayServer(local_server).environment("MIR_SERVER_DISPLAY_CONFIG", f"static={CONFIG_FILE}")
        on_scale = Mock()
        watcher = OutputWatcher(server.display_name, on_scale=on_scale)

        async with server, watcher:
            yaml = importlib.import_module("yaml")
            await asyncio.sleep(short_wait_time)
            with open(CONFIG_FILE, "r") as file:
                # the yaml parser doesn't like tabs before our comments
                content = file.read().replace("\t#", "  #")
                data = yaml.safe_load(content)

            card = data["layouts"]["default"]["cards"][0]
            for k in card:
                if type(card[k]) is dict:
                    card[k]["scale"] = 2
                    break

            with open(CONFIG_FILE, "w") as file:
                yaml.dump(data, file)
            await asyncio.sleep(short_wait_time)

        on_scale.assert_called_with(ANY, 2)
