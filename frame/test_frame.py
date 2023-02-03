from frame_test_case import DisplayServer
from unittest import TestCase
import time

class FrameSmokeTests(TestCase):
    def test_frame_can_run(self) -> None:
        with DisplayServer('ubuntu-frame') as server:
            pass
