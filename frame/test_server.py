from unittest import TestCase

from parameterized import parameterized
from helpers import all_servers

from display_server import DisplayServer

class ServerSmokeTests(TestCase):
    @parameterized.expand(
        (s for s in all_servers())
    )
    def test_server_can_run(self, server) -> None:
        with DisplayServer(server) as server:
            pass
