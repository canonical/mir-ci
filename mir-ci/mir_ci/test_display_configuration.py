import asyncio
import importlib
import os
import tempfile
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
            # TODO: Test other servers. Frame-based servers use
            # a configuration file that is within the snap, so it
            # is unclear how to read/modify that file from the outside
            apps.mir_demo_server(),
        ],
    )
    @pytest.mark.deps(pip_pkgs=("pyyaml",))
    async def test_can_update_scale(self, local_server) -> None:
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_filename = tmp_file.name
        try:
            os.remove(tmp_filename)
        except OSError:
            pass

        server = DisplayServer(local_server, env={"MIR_SERVER_DISPLAY_CONFIG": f"static={tmp_filename}"})
        on_scale = Mock()
        watcher = OutputWatcher(server.display_name, on_scale=on_scale)

        async with server, watcher:
            yaml = importlib.import_module("yaml")
            await asyncio.sleep(short_wait_time)
            with open(tmp_filename, "r") as file:
                # the yaml parser doesn't like tabs before our comments
                content = file.read().replace("\t#", "  #")
                data = yaml.safe_load(content)

            card = data["layouts"]["default"]["cards"][0]
            for k in card:
                if type(card[k]) is dict:
                    card[k]["scale"] = 2
                    break

            with open(tmp_filename, "w") as file:
                yaml.dump(data, file)
            await asyncio.sleep(short_wait_time)

        on_scale.assert_called_with(ANY, 2)
