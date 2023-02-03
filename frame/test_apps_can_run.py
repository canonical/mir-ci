from frame_test_case import DisplayServer
from parameterized import parameterized_class
from unittest import TestCase
import time

short_wait_time = 3

@parameterized_class([
    {'server': 'ubuntu-frame', 'app': 'wpe-webkit-mir-kiosk.cog'},
    {'server': 'ubuntu-frame', 'app': 'mir-kiosk-neverputt'},
    {'server': 'ubuntu-frame', 'app': 'mir-kiosk-scummvm'},
    {'server': 'ubuntu-frame', 'app': 'mir-kiosk-kodi'},
    {'server': 'ubuntu-frame', 'app': 'gedit'},
    {'server': 'ubuntu-frame', 'app': 'qterminal'},
    {'server': 'mir-kiosk', 'app': 'wpe-webkit-mir-kiosk.cog'},
    {'server': 'mir-kiosk', 'app': 'mir-kiosk-neverputt'},
    {'server': 'mir-kiosk', 'app': 'mir-kiosk-scummvm'},
    {'server': 'mir-kiosk', 'app': 'mir-kiosk-kodi'},
    {'server': 'mir-kiosk', 'app': 'gedit'},
    {'server': 'mir-kiosk', 'app': 'qterminal'},
    {'server': 'egmde', 'app': 'wpe-webkit-mir-kiosk.cog'},
    {'server': 'egmde', 'app': 'mir-kiosk-neverputt'},
    {'server': 'egmde', 'app': 'mir-kiosk-scummvm'},
    {'server': 'egmde', 'app': 'mir-kiosk-kodi'},
    {'server': 'egmde', 'app': 'gedit'},
    {'server': 'egmde', 'app': 'qterminal'},
])
class TestAppsCanRun(TestCase):
    def test_app_can_run(self) -> None:
        with DisplayServer(self.server) as server:
            app = server.program(self.app)
            time.sleep(short_wait_time)
            app.assert_running()
