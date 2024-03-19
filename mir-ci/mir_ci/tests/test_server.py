import pytest
from mir_ci.program.display_server import DisplayServer


class TestServerCanRun:
    @pytest.mark.smoke
    async def test_server_can_run(self, mir_server) -> None:
        async with DisplayServer(mir_server) as mir_server:
            pass
