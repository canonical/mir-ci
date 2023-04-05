from display_server import DisplayServer

class TestServerCanRun:
    def test_server_can_run(self, server) -> None:
        with DisplayServer(server) as server:
            pass
