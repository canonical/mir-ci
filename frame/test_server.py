from helpers import all_servers
from display_server import DisplayServer
import pytest

class TestServerCanRun:
    @pytest.mark.parametrize('server', all_servers())
    def test_server_can_run(self, server) -> None:
        with DisplayServer(server) as server:
            pass
