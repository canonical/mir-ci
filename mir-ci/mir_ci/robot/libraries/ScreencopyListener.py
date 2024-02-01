import asyncio
from pathlib import Path

from typing import Optional
from mir_ci.robot.libraries.Screencopy import Screencopy

class ScreencopyListener():

    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self,
                 name: str,
                 output_path: Optional[Path] = None,
                 delete_screenshots: bool = False):
        self.name = name
        self.output_path = output_path
        self.delete_screenshots = delete_screenshots
        self.screencopy = None

    def start_test(self, name, attrs):  # pylint: disable=unused-argument
        self.screencopy = Screencopy()

    def start_keyword(self, name, attrs):  # pylint: disable=unused-argument
        self._take_screenshot()

    def end_keyword(self, name, attrs):  # pylint: disable=unused-argument
        self._take_screenshot()

    def end_test(self, name, attrs):  # pylint: disable=unused-argument
        self._take_screenshot()
        self._create_video()

    def close(self):
        if not self.screencopy:
            return
        self._run_coroutine(self.screencopy.disconnect())
        self.screencopy = None

    def _run_coroutine(self, coro):
        asyncio.get_event_loop().run_until_complete(coro)

    def _take_screenshot(self):
        if not self.screencopy:
            return
        self._run_coroutine(self.screencopy.take_screenshot(self.name, self.output_path))

    def _create_video(self):
        if not self.screencopy:
            return
        self._run_coroutine(self.screencopy.create_video_from_screenshots(self.output_path,
                                                                          None,
                                                                          self.delete_screenshots))
        self._run_coroutine(self.screencopy.disconnect())
        self.close()
