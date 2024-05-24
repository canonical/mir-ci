import asyncio
import base64
import math
import time
from asyncio import open_connection
from enum import IntEnum
from io import BytesIO
from typing import List, Optional, Tuple

import asyncvnc
from PIL import Image
from robot.api import logger
from robot.api.deco import keyword, library
from RPA.Images import Images
from RPA.recognition.templates import ImageNotFoundError


class Button(IntEnum):
    LEFT = 0
    RIGHT = 1
    MIDDLE = 2


@library(scope="TEST")
class Vnc:
    """
    A Robot Framework library for interacting with HIDs through VNC.
    """

    ROBOT_LISTENER_API_VERSION = 3
    TOLERANCE = 0.8

    def __init__(
        self, host="localhost", port=5900, username: Optional[str] = None, password: Optional[str] = None
    ) -> None:
        self.ROBOT_LIBRARY_LISTENER = self
        self._client: asyncvnc.Client = None
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._pointer_position: Optional[Tuple[int, int]] = None
        self._rpa_images = Images()

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
        await self.connect()
        regions = []
        end_time = time.time() + float(timeout)
        screenshot = None
        while time.time() <= end_time:
            screenshot = Image.fromarray(await asyncio.wait_for(self._client.screenshot(), timeout))
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

    @keyword
    async def type_string(self, text: str):
        await self.connect()
        self._client.keyboard.write(text)

    @keyword
    async def move_pointer_to_absolute(self, x: int, y: int) -> None:
        await self.connect()
        self._client.mouse.move(x, y)
        self._pointer_position = (x, y)

    @keyword
    async def move_pointer_to_proportional(self, x: float, y: float) -> tuple[int, int]:
        await self.connect()
        absolute_position = self.get_absolute_from_proportional(x, y)
        self.move_pointer_to_absolute(absolute_position[0], absolute_position[1])
        return absolute_position

    @keyword
    async def walk_pointer_to_absolute(self, x: int, y: int, step_distance: int, delay: float) -> None:
        await self.connect()
        assert step_distance > 0, "Step distance must be positive"

        if self._pointer_position is None:
            self._pointer_position = (0, 0)
            self._client.mouse.move(self._pointer_position[0], self._pointer_position[1])

        distance = ((self._pointer_position[0] - x) ** 2 + (self._pointer_position[1] - y) ** 2) ** 0.5
        if distance == 0:
            return
        steps = math.ceil(distance / step_distance)

        for step in range(0, steps + 1):
            t = step / steps
            walk_x = (1 - t) * self._pointer_position[0] + t * x
            walk_y = (1 - t) * self._pointer_position[1] + t * y
            self._client.mouse.move(int(walk_x), int(walk_y))
            await asyncio.sleep(delay)

        self._pointer_position = (x, y)

    @keyword
    async def walk_pointer_to_proportional(
        self, x: float, y: float, step_distance: int, delay: float
    ) -> tuple[int, int]:
        await self.connect()
        absolute_position = self.get_absolute_from_proportional(x, y)
        await self.walk_pointer_to_absolute(absolute_position[0], absolute_position[1], step_distance, delay)
        return absolute_position

    @keyword
    async def press_pointer_button(self, button: str) -> None:
        await self.connect()
        mask = 1 << Button[button]
        self._client.mouse.buttons |= mask
        self._client.mouse._write()

    @keyword
    async def release_pointer_button(self, button: str) -> None:
        await self.connect()
        mask = 1 << Button[button]
        self._client.mouse.buttons &= ~mask
        self._client.mouse._write()

    @keyword
    async def click_pointer_button(self, button: str) -> None:
        await self.connect()
        self._client.mouse.click(Button[button])

    @keyword
    async def release_buttons(self) -> None:
        await self.connect()
        self._client.mouse.buttons = 0
        self._client.mouse._write()

    def get_absolute_from_proportional(self, x: float, y: float) -> tuple[int, int]:
        """
        Get the absolute position for the given output size proportions.

        :param x: Output-relative x-coordinate in the range 0..1, where 0
                  represents the left edge, and 1 represents the right edge of
                  the output.
        :param y: Output-relative y-coordinate in the range 0..1, where 0
                  represents the top edge, and 1 represents the bottom edge
                  of the output.
        :return tuple containing the corresponding absolute x and y coordinates.
        """
        assert 0 <= x <= 1, "x not in range 0..1"
        assert 0 <= y <= 1, "y not in range 0..1"
        assert self._client.video.width > 0, "Output width must be greater than 0"
        assert self._client.video.height > 0, "Output height must be greater than 0"
        return (int(x * self._client.video.width), int(y * self._client.video.height))

    async def connect(self):
        if not self._client:
            reader, writer = await open_connection(self._host, self._port)
            self._client = await asyncvnc.Client.create(reader, writer, self._username, self._password)

    async def disconnect(self):
        if self._client:
            await self._client.drain()

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

    def _close(self):
        """Listener method called when the library goes out of scope."""
        asyncio.get_event_loop().run_until_complete(self.disconnect())
