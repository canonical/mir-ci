import asyncio
import os
import time

from PIL import Image
from RPA.Images import Images
from RPA.recognition.templates import ImageNotFoundError
from mir_ci.screencopy_tracker import ScreencopyTracker
from robot.api.deco import keyword, library


@library(scope="GLOBAL")
class Screencopy(ScreencopyTracker):

    ROBOT_LISTENER_API_VERSION = 3
    TOLERANCE = 0.8

    def __init__(self) -> None:
        self.ROBOT_LIBRARY_LISTENER = self
        display_name = os.environ.get("WAYLAND_DISPLAY", "wayland-0")
        super().__init__(display_name)
        self._rpa_images = Images()

    @keyword
    async def save_frame(self):
        await self.connect()
        try:
            screenshot = self.grab_screenshot()
            screenshot.save(f"frame_{self.frame_count}.png")
        except (RuntimeError, ValueError, ImageNotFoundError) as exc:
            raise ImageNotFoundError from exc

    @keyword
    async def test_match(self, template: str):
        await self.connect()
        try:
            screenshot = self.grab_screenshot()
            self._rpa_images.find_template_in_image(
                screenshot,
                template,
                tolerance=self.TOLERANCE,
            )
        except (RuntimeError, ValueError, ImageNotFoundError) as exc:
            raise ImageNotFoundError from exc

    @keyword
    async def wait_match(self, template: str, timeout: int = 10):
        await self.connect()
        match_status = False
        screenshot = None
        end_time = time.time() + float(timeout)
        while time.time() < end_time:
            try:
                screenshot = self.grab_screenshot()
                self._rpa_images.find_template_in_image(
                    screenshot,
                    template,
                    tolerance=self.TOLERANCE,
                )
                match_status = True
                break
            except (RuntimeError, ValueError, ImageNotFoundError):
                continue

        if match_status:
            return

        raise ImageNotFoundError

    def grab_screenshot(self) -> Image:
        assert self.shm_data is not None, "No SHM data available"

        self.shm_data.seek(0)
        data = self.shm_data.read()
        size = (self.buffer_width, self.buffer_height)
        stride = self.buffer_stride
        image = Image.frombytes("RGBA", size, data, "raw", "RGBA", stride, -1)

        return image

    async def connect(self):
        """Connect to the display."""
        if not self.shm_data:
            await super().connect()
            while self.frame_count == 0:
                await asyncio.sleep(0)

    async def disconnect(self):
        """Disconnect from the display."""
        if self.shm_data:
            await super().disconnect()

    def _close(self):
        """Listener method called when the library goes out of scope."""
        asyncio.get_event_loop().run_until_complete(self.disconnect())
