import asyncio
import base64
import os
import time

from io import BytesIO
from typing import List

from PIL import Image
from RPA.Images import Images
from RPA.recognition.templates import ImageNotFoundError

from mir_ci.screencopy_tracker import ScreencopyTracker
from robot.api import logger
from robot.api.deco import keyword, library


@library(scope="GLOBAL")
class Screencopy(ScreencopyTracker):
    """
    A Robot Framework library for capturing screenshots from the 
    Wayland display and performing image template matching.

    The client connects to the display upon entering the first keyword,
    and disconnects when the library goes out of scope.

    If WAYLAND_DISPLAY is not defined, it defaults to 'wayland-0'.
    """

    ROBOT_LISTENER_API_VERSION = 3
    TOLERANCE = 0.8

    def __init__(self) -> None:
        self.ROBOT_LIBRARY_LISTENER = self
        display_name = os.environ.get("WAYLAND_DISPLAY", "wayland-0")
        super().__init__(display_name)
        self._rpa_images = Images()

    @keyword
    async def test_match(self, template: str):
        """
        Grab a screenshot and check for a match with the given template.

        :param template: path to an image file to be used as template
        :return: list of matched regions
        :raises ImageNotFoundError: if no match is found
        """
        await self.connect()
        screenshot = None

        try:
            screenshot = self.grab_screenshot()
            regions = self._rpa_images.find_template_in_image(
                screenshot,
                template,
                tolerance=self.TOLERANCE,
            )

            return [
                {
                    "left": region.left,
                    "top": region.top,
                    "right": region.right,
                    "bottom": region.bottom,
                }
                for region in regions
            ]
        except (RuntimeError, ValueError, ImageNotFoundError) as exc:
            self._log_failed_match(screenshot, template)
            raise ImageNotFoundError from exc

    @keyword
    async def wait_match(self, template: str, timeout: int = 10) -> List[dict]:
        """
        Grab screenshots and compare until there's a match with the provided
        template.

        :param template: path to an image file to be used as template
        :param timeout: timeout in seconds
        :return: list of matched regions
        :raises ImageNotFoundError: if no match is found within the timeout
        """
        await self.connect()
        regions = []
        last_frame_count = 0
        matched = False
        screenshot = None
        end_time = time.time() + float(timeout)
        while time.time() < end_time:
            if self.frame_count == last_frame_count:
                await asyncio.sleep(0)
            else:
                last_frame_count = self.frame_count
                try:
                    screenshot = self.grab_screenshot()
                    regions = self._rpa_images.find_template_in_image(
                        screenshot,
                        template,
                        tolerance=self.TOLERANCE,
                    )
                    matched = True
                    break
                except (RuntimeError, ValueError, ImageNotFoundError):
                    continue

        if not matched:
            self._log_failed_match(screenshot, template)
            raise ImageNotFoundError

        return [
            {
                "left": region.left,
                "top": region.top,
                "right": region.right,
                "bottom": region.bottom,
            }
            for region in regions
        ]

    def grab_screenshot(self) -> Image.Image:
        """Grab the latest captured frame from the display."""
        assert self.shm_data is not None, "No SHM data available"

        self.shm_data.seek(0)
        data = self.shm_data.read()
        size = (self.buffer_width, self.buffer_height)
        stride = self.buffer_stride
        image = Image.frombytes("RGBA", size, data, "raw", "RGBA", stride, -1)
        b, g, r, a, *_ = image.split()
        image = Image.merge("RGBA", (r, g, b, a))

        return image

    async def connect(self):
        """Connect to the display."""
        if not self.shm_data:
            await super().connect()
            # Wait for the first frame to become ready
            while self.frame_count == 0:
                await asyncio.sleep(0)

    async def disconnect(self):
        """Disconnect from the display."""
        if self.shm_data:
            await super().disconnect()

    @staticmethod
    def _to_base64(image: Image.Image) -> str:
        """Convert Pillow Image to b64"""
        im_file = BytesIO()
        image.save(im_file, format="PNG")
        im_bytes = im_file.getvalue()
        im_b64 = base64.b64encode(im_bytes)
        return im_b64.decode()

    def _log_failed_match(self, screenshot, template):
        """Log a failure with template matching."""
        if not screenshot:
            return

        template_img = Image.open(template)
        template_string = (
            'Template was:<br><img src="data:image/png;base64,'
            f'{self._to_base64(template_img)}" /><br>'
        )
        image_string = (
            'Image was:<br><img src="data:image/png;base64,'
            f'{self._to_base64(screenshot)}" />'
        )
        logger.info(
            template_string + image_string,
            html=True,
        )

    def _close(self):
        """Listener method called when the library goes out of scope."""
        asyncio.get_event_loop().run_until_complete(self.disconnect())
