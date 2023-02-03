from frame_test_case import FrameTestCase
import time

short_wait_time = 5

class TestAppsCanRun(FrameTestCase):
    def run_test(self, command: str) -> None:
        app = self.program(command)
        time.sleep(short_wait_time)
        app.assert_running()

    def test_wpe_webkit(self) -> None:
        self.run_test('wpe-webkit-mir-kiosk.cog')

    def test_neverputt(self) -> None:
        self.run_test('mir-kiosk-neverputt')

    def test_scummvm(self) -> None:
        self.run_test('mir-kiosk-scummvm')

    def test_kodi(self) -> None:
        self.run_test('mir-kiosk-kodi')
