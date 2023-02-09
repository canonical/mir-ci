from frame_test_case import DisplayServer
from parameterized import parameterized
from unittest import TestCase
import time

short_wait_time = 3

class TestAppsCanRun(TestCase):
    @parameterized.expand([
        ('ubuntu-frame', 'wpe-webkit-mir-kiosk.cog'),
        ('ubuntu-frame', 'mir-kiosk-neverputt'),
        ('ubuntu-frame', 'mir-kiosk-scummvm'),
        ('ubuntu-frame', 'mir-kiosk-kodi'),
        ('ubuntu-frame', 'gedit'),
        ('ubuntu-frame', 'qterminal'),
        ('mir-kiosk', 'wpe-webkit-mir-kiosk.cog'),
        ('mir-kiosk', 'mir-kiosk-neverputt'),
        ('mir-kiosk', 'mir-kiosk-scummvm'),
        ('mir-kiosk', 'mir-kiosk-kodi'),
        ('mir-kiosk', 'gedit'),
        ('mir-kiosk', 'qterminal'),
        ('egmde', 'wpe-webkit-mir-kiosk.cog'),
        ('egmde', 'mir-kiosk-neverputt'),
        ('egmde', 'mir-kiosk-scummvm'),
        ('egmde', 'mir-kiosk-kodi'),
        ('egmde', 'gedit'),
        ('egmde', 'qterminal'),
    ])
    def test_app_can_run(self, server, app) -> None:
        with DisplayServer(server) as server:
            app = server.program(app)
            time.sleep(short_wait_time)
            app.assert_running()
