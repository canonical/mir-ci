import asyncio
import math
import os
from typing import Optional, Tuple

from mir_ci.wayland.virtual_pointer import Button, VirtualPointer
from robot.api.deco import keyword, library


@library(scope="TEST")
class WaylandHid(VirtualPointer):
    """
    A Robot Framework library for interacting with virtual Wayland-based HIDs.

    The client connects to the display upon entering the first keyword,
    and disconnects when the library goes out of scope.

    If WAYLAND_DISPLAY is not defined, it defaults to 'wayland-0'.
    """

    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self) -> None:
        self.ROBOT_LIBRARY_LISTENER = self
        self._pointer_position: Optional[Tuple[int, int]] = None
        display_name = os.environ.get("WAYLAND_DISPLAY", "wayland-0")
        super().__init__(display_name)

    @keyword
    async def move_pointer_to_absolute(self, x: int, y: int) -> None:
        await self.connect()
        self.move_to_absolute(x, y)
        self._pointer_position = (x, y)

    @keyword
    async def move_pointer_to_proportional(self, x: float, y: float) -> tuple[int, int]:
        await self.connect()
        self.move_to_proportional(x, y)
        absolute_position = self.get_absolute_from_proportional(x, y)
        self._pointer_position = absolute_position
        return absolute_position

    @keyword
    async def walk_pointer_to_absolute(self, x: int, y: int, step_distance: int, delay: float) -> None:
        await self.connect()
        assert step_distance > 0, "Step distance must be positive"

        if self._pointer_position is None:
            self._pointer_position = (0, 0)
            self.move_to_absolute(self._pointer_position[0], self._pointer_position[1])

        distance = ((self._pointer_position[0] - x) ** 2 + (self._pointer_position[1] - y) ** 2) ** 0.5
        if distance == 0:
            return
        steps = math.ceil(distance / step_distance)

        for step in range(0, steps + 1):
            t = step / steps
            walk_x = (1 - t) * self._pointer_position[0] + t * x
            walk_y = (1 - t) * self._pointer_position[1] + t * y
            self.move_to_absolute(walk_x, walk_y)
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
        self.button(Button[button], True)

    @keyword
    async def release_pointer_button(self, button: str) -> None:
        await self.connect()
        self.button(Button[button], False)

    @keyword
    async def click_pointer_button(self, button: str) -> None:
        await self.connect()
        self.button(Button[button], True)
        self.button(Button[button], False)

    @keyword
    async def release_buttons(self) -> None:
        await self.connect()
        for button in Button:
            self.button(button, False)

    def get_absolute_from_proportional(self, x: float, y: float) -> tuple[int, int]:
        """
        Get the absolute position for the given output size proportions.

        :param x: Output-relative x-coordinate in the range 0..1, where 0
                  represents the left edge, and 1 represents the right edge of
                  the output.
        :param y: Output-relative y-coordinate in the range 0..1, where 0
                  represents
                  the top edge, and 1 represents the bottom edge of the output.
        :return tuple containing the corresponding absolute x and y coordinates.
        """
        assert 0 <= x <= 1, "x not in range 0..1"
        assert 0 <= y <= 1, "y not in range 0..1"
        assert self.output_width > 0, "Output width must be greater than 0"
        assert self.output_height > 0, "Output height must be greater than 0"
        return (int(x * self.output_width), int(y * self.output_height))

    async def connect(self):
        """Connect to the display."""
        if not self.pointer:
            await super().connect()

    async def disconnect(self):
        """Disconnect from the display."""
        if self.pointer:
            await super().disconnect()

    def _close(self):
        """Listener method called when the library goes out of scope."""
        asyncio.get_event_loop().run_until_complete(self.disconnect())
