from display_server import DisplayServer
from parameterized import parameterized
from unittest import TestCase
from helpers import all_servers
from program import AppFixture
import itertools
import os


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
    ]))
    def test_app_can_run(self, server, app) -> None:
        with DisplayServer(server) as s, app[0] as a:
            with s.program(a) as p:
                p.wait(app[1])
