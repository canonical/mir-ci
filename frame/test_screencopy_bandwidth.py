from display_server import DisplayServer
from screencopy_tracker import ScreencopyTracker
from helpers import all_servers
from program import AppFixture, appids
import pytest
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

class TestScreencopyBandwidth:
    @pytest.mark.parametrize('server', all_servers())
    @pytest.mark.parametrize('app', [
        (QTerminal('--execute', f'asciinema play {ASCIINEMA_CAST}', id='asciinema'), 15),
        (AppFixture("mir-kiosk-neverputt"), None),
    ], ids=lambda x: appids(x[0]))
    def test_active_app(self, record_property, server, app) -> None:
        with DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions) as s, app[0] as a:
            tracker = ScreencopyTracker(s.display_name)
            with tracker, s.program(a) as p:
                if app[1] is not None:
                    p.wait(app[1])
                else:
                    time.sleep(long_wait_time)
            for name, val in tracker.properties().items():
                record_property(name, val)

    @pytest.mark.parametrize('server', all_servers())
    def test_compositor_alone(self, record_property, server) -> None:
        with DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions) as s:
            tracker = ScreencopyTracker(s.display_name)
            with tracker:
                time.sleep(long_wait_time)
            for name, val in tracker.properties().items():
                record_property(name, val)

    @pytest.mark.parametrize('server', all_servers())
    @pytest.mark.parametrize('app', [
        "qterminal",
        ("gedit", "-s"),
        "mir-kiosk-kodi",
    ], ids=appids)
    def test_inactive_app(self, record_property, server, app) -> None:
        with DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions) as s:
            tracker = ScreencopyTracker(s.display_name)
            with tracker, s.program(app):
                time.sleep(long_wait_time)
            for name, val in tracker.properties().items():
                record_property(name, val)
