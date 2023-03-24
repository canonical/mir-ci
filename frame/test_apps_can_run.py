from display_server import DisplayServer
from helpers import all_servers
import pytest
import time

short_wait_time = 3

class TestAppsCanRun:
    @pytest.mark.parametrize('server', all_servers())
    @pytest.mark.parametrize('app', [
        'wpe-webkit-mir-kiosk.cog',
        'mir-kiosk-neverputt',
        'mir-kiosk-scummvm',
        'mir-kiosk-kodi',
        ('gedit', '-s'), # -s prevents multiple instances from using the same process/window/display
        'qterminal',
    ])
    def test_app_can_run(self, server, app) -> None:
        with DisplayServer(server) as server:
            with server.program(app) as app:
                time.sleep(short_wait_time)
