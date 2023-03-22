from display_server import DisplayServer
from parameterized import parameterized
from unittest import TestCase
from helpers import all_servers
import itertools
import os


ASCIINEMA_CAST = f'{os.path.dirname(__file__)}/data/demo.cast'

class TestScreencopyBandwidth(TestCase):
    @parameterized.expand(itertools.product(all_servers(), [
        (('qterminal', '--execute', f'asciinema play {ASCIINEMA_CAST}'), 30),
    ]))
    def test_app_can_run(self, server, app) -> None:
        with DisplayServer(server) as s:
            with s.program(app[0]) as a:
                a.wait(app[1])
