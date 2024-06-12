import asyncio
import base64
import os
import shutil
import subprocess
import tempfile
import time
from io import BytesIO
from typing import List

from mir_ci.wayland.screencopy_tracker import ScreencopyTracker
from PIL import Image
from robot.api import logger
from robot.api.deco import keyword, library
from RPA.Images import Images
from RPA.recognition.templates import ImageNotFoundError


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

    def _start_suite(self, data, result) -> None:
        self._screenshots_dir = tempfile.mkdtemp()

    @keyword
    async def match(self, template: str, timeout: int = 5) -> List[dict]:
        """
        Grab screenshots and compare until there's a match with the provided
        template.

        :param template: path to an image file to be used as template
        :param timeout: timeout in seconds
        :return: list of matched regions
        :raises ImageNotFoundError: if no match is found within the timeout
        """
        regions = []
        end_time = time.time() + float(timeout)
        last_checked_frame_count = 0
        screenshot = None
        while time.time() <= end_time:
            frame_count, screenshot = await asyncio.wait_for(self.grab_screenshot(), timeout)
            if last_checked_frame_count != frame_count:
                last_checked_frame_count = frame_count
                try:
                    regions = self._rpa_images.find_template_in_image(
                        screenshot,
                        template,
                        tolerance=self.TOLERANCE,
                    )
                except (RuntimeError, ValueError, ImageNotFoundError):
                    continue
                else:
                    break
        else:
            if screenshot:
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

    async def grab_screenshot(self):
        """
        Grabs the current frame tracked by the screencopy tracker.

        :return Tuple (frame count, Pillow Image of the frame)
        """
        await self.connect()

        # Wait for the first frame
        while self.frame_count == 0:
            await asyncio.sleep(0)

        assert self.shm_data is not None, "No SHM data available"
        self.shm_data.seek(0)
        data = self.shm_data.read()
        size = (self.buffer_width, self.buffer_height)
        assert all(dim > 0 for dim in size), "Not enough image data"
        stride = self.buffer_stride
        image = Image.frombytes("RGBA", size, data, "raw", "RGBA", stride, -1)
        b, g, r, a, *_ = image.split()
        image = Image.merge("RGBA", (r, g, b, a))
        image.save(f"{self._screenshots_dir}/{self.frame_count:010d}.png", compress_level=1)

        return (self.frame_count, image)

    async def connect(self):
        """Connect to the display."""
        if not self.shm_data:
            await super().connect()

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
        template_img = Image.open(template)
        template_string = (
            'Template was:<br /><img style="max-width: 100%" src="data:image/png;base64,'
            f'{self._to_base64(template_img)}" /><br />'
        )
        image_string = (
            'Image was:<br /><img style="max-width: 100%" src="data:image/png;base64,'
            f'{self._to_base64(screenshot)}" />'
        )
        logger.info(
            template_string + image_string,
            html=True,
        )

    def _end_suite(self, data, result) -> None:
        if not result.passed:
            video_path = f"{self._screenshots_dir}/video.webm"
            try:
                subprocess.run(
                    (
                        "ffmpeg",
                        "-f",
                        "image2",
                        "-r",
                        "5",
                        "-pattern_type",
                        "glob",
                        "-i",
                        f"{self._screenshots_dir}/*.png",
                        video_path,
                    ),
                    capture_output=True,
                    check=True,
                )
            except (FileNotFoundError, PermissionError, subprocess.CalledProcessError) as ex:
                logger.warn(ex)
            else:
                with open(video_path, "rb") as f:
                    logger.error(
                        '<video controls style="max-width: 50%" src="data:video/webm;base64,'
                        f'{base64.b64encode(f.read()).decode()}" />',
                        html=True,
                    )
        shutil.rmtree(self._screenshots_dir)

    def _close(self):
        """Listener method called when the library goes out of scope."""
        asyncio.get_event_loop().run_until_complete(self.disconnect())
