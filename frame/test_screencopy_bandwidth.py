from display_server import DisplayServer
from parameterized import parameterized
from unittest import TestCase
from helpers import all_servers
from program import AppFixture
import itertools
import os
import time

long_wait_time = 10

ASCIINEMA_CAST = f'{os.path.dirname(__file__)}/data/demo.cast'


class QTerminal(AppFixture):
    executable = 'qterminal'

    def env(self) -> dict[str, str]:
        env = super().env()
        config = self.temppath / 'qterminal.org' / 'qterminal.ini'
        config.parent.mkdir(parents=True)
        with open(config, 'w') as c:
            c.write('[General]\nAskOnExit=false')

        return env | {
            'XDG_CONFIG_HOME': str(self.temppath)
        }


class TestScreencopyBandwidth(TestCase):
    @parameterized.expand(itertools.product(all_servers(), [
        (QTerminal('--execute', f'asciinema play {ASCIINEMA_CAST}'), 15),
        (AppFixture("mir-kiosk-neverputt"), None),
    ]))
    def test_active_app(self, server, app) -> None:
        with DisplayServer(server) as s, app[0] as a:
            with s.program(a) as p:
                if app[1] is not None:
                    p.wait(app[1])
                else:
                    time.sleep(long_wait_time)

    @parameterized.expand(all_servers())
    def test_compositor_alone(self, server) -> None:
        with DisplayServer(server) as s:
            time.sleep(long_wait_time)

    @parameterized.expand(itertools.product(all_servers(), [
        "qterminal",
        ("gedit", "-s"),
        "mir-kiosk-kodi",
    ]))
    def test_inactive_app(self, server, app) -> None:
        with DisplayServer(server) as s:
            with s.program(app):
                time.sleep(long_wait_time)
