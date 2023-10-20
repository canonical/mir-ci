import asyncio
import importlib
import os

import pytest
from mir_ci import SLOWDOWN, apps
from mir_ci.display_server import DisplayServer

short_wait_time = 1 * SLOWDOWN


class TestDisplayConfiguration:
    @pytest.mark.parametrize(
        "server",
        [
            apps.mir_demo_server(),
        ],
    )
    @pytest.mark.deps(pip_pkgs=("pyyaml",))
    async def test_can_update_scale(self, server) -> None:
        CONFIG_FILE = "/tmp/mir_ci_display_config.yaml"
        try:
            os.remove(CONFIG_FILE)
        except OSError:
            pass
        server = DisplayServer(server).environment("MIR_SERVER_DISPLAY_CONFIG", f"static={CONFIG_FILE}")

        async with server:
            yaml = importlib.import_module("yaml")
            await asyncio.sleep(short_wait_time)
            with open(CONFIG_FILE, "r") as file:
                # the yaml parser doesn't like tabs before our comments
                content = file.read().replace("\t#", "  #")
                data = yaml.safe_load(content)

            data["layouts"]["default"]["cards"][0]["unknown-1"]["scale"] = "2"
            with open(CONFIG_FILE, "w") as file:
                yaml.dump(data, file)
            await asyncio.sleep(short_wait_time)

        assert "New display configuration:" in server.server.output
        assert "New base display configuration:" in server.server.output
