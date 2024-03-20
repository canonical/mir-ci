import pytest
from mir_ci.program.display_server import DisplayServer


class TestServerCanRun:
    @pytest.mark.smoke
    async def test_server_can_run(self, any_server) -> None:
        async with DisplayServer(any_server) as any_server:
            pass
