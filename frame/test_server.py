import pytest

from display_server import DisplayServer

class TestServerCanRun:
    @pytest.mark.smoke
    def test_server_can_run(self, server) -> None:
        with DisplayServer(server) as server:
            pass
