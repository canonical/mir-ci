from frame_test_case import FrameTestCase
import time

short_wait_time = 1

class FrameSmokeTests(FrameTestCase):
    def test_frame_can_run(self) -> None:
        pass

    def test_wpe_webkit_can_run(self) -> None:
        app = self.program('wpe-webkit-mir-kiosk.cog')
        time.sleep(short_wait_time)
        app.assert_running()

    def test_neverputt_can_run(self) -> None:
        app = self.program('mir-kiosk-neverputt')
        time.sleep(short_wait_time)
        app.assert_running()
