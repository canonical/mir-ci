import pytest

from mir_ci.display_server import DisplayServer

class TestServerCanRun:
    @pytest.mark.smoke
    async def test_server_can_run(self, server) -> None:
        async with DisplayServer(server) as server:
            pass
