from display_server import DisplayServer
from parameterized import parameterized
from unittest import TestCase
from helpers import combine, all_servers
import time

short_wait_time = 3

class TestAppsCanRun(TestCase):
    @parameterized.expand(combine(all_servers(), [
        'wpe-webkit-mir-kiosk.cog',
        'mir-kiosk-neverputt',
        'mir-kiosk-scummvm',
        'mir-kiosk-kodi',
        'gedit',
        'qterminal',
    ]))
    def test_app_can_run(self, server, app) -> None:
        with DisplayServer(server) as server:
            with server.program(app) as app:
                time.sleep(short_wait_time)
