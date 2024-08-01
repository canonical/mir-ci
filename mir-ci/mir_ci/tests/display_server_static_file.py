import importlib
import os
import tempfile
from typing import Any
from mir_ci.program.display_server import DisplayServer

class DisplayServerStaticFile:
    def __init__(self, local_server, *args, **kwargs):
        self.local_server = local_server
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        self.tmp_filename = tmp_file.name
        try:
            os.remove(self.tmp_filename)
        except OSError:
            pass

        config_file = f"static={self.tmp_filename}"
        self.server = DisplayServer(self.local_server, env={"MIR_SERVER_DISPLAY_CONFIG": config_file}, *args, **kwargs)

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
