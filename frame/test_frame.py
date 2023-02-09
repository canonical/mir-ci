from unittest import TestCase
import time

from display_server import DisplayServer

class FrameSmokeTests(TestCase):
    def test_frame_can_run(self) -> None:
        with DisplayServer('ubuntu-frame') as server:
            pass
