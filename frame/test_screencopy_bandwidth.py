from display_server import DisplayServer
from parameterized import parameterized
from unittest import TestCase
from helpers import all_servers
import itertools
import tempfile
import os


ASCIINEMA_CAST = f'{os.path.dirname(__file__)}/data/demo.cast'

class TestScreencopyBandwidth(TestCase):
    @parameterized.expand(itertools.product(all_servers(), [
        (('qterminal', '--execute', f'asciinema play {ASCIINEMA_CAST}'), 30),
    ]))
    def test_app_can_run(self, server, app) -> None:
        with DisplayServer(server) as s, tempfile.TemporaryDirectory() as d:
            env = {
                'XDG_DATA_HOME': f"{d}/data",
                'XDG_CONFIG_HOME': f"{d}/config",
            }
            with s.program(app[0], env) as a:
                a.wait(app[1])
