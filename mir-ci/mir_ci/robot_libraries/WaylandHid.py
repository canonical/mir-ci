import asyncio
import os
from typing import Dict

from mir_ci.virtual_pointer import Button, VirtualPointer
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
        self.pointer_position = {"x": 0.0, "y": 0.0}
        display_name = os.environ.get("WAYLAND_DISPLAY", "wayland-0")
        super().__init__(display_name)

    @keyword
    async def move_pointer_to_absolute(self, x: float, y: float) -> None:
        """Move the virtual pointer to an absolute position within the output."""
        await self.connect()
        self.move_to_absolute(x, y)
        self.pointer_position = {"x": x, "y": y}

    @keyword
    async def move_pointer_to_proportional(self, x: float, y: float) -> None:
        """Move the virtual pointer to a position proportional to the size of the output."""
        await self.connect()
        self.move_to_proportional(x, y)
        absolute_position = await self.get_absolute_from_proportional(x, y)
        self.pointer_position = absolute_position

    @keyword("Press ${button} Button")
    async def press_pointer_button(self, button: str) -> None:
        """Press a button (LEFT|RIGHT|MIDDLE) on the virtual pointer."""
        await self.connect()
        self.button(Button[button], True)

    @keyword("Release ${button} Button")
    async def release_pointer_button(self, button: str) -> None:
        """Release a button (LEFT|RIGHT|MIDDLE) on the virtual pointer."""
        await self.connect()
        self.button(Button[button], False)

    @keyword
    async def release_buttons(self) -> None:
        """Release all buttons on the virtual pointer."""
        await self.connect()
        for button in Button:
            self.button(button, False)

    @keyword
    async def get_absolute_from_proportional(self, x: float, y: float) -> Dict[str, float]:
        """Get the absolute position for the given output size proportions."""
        await self.connect()
        assert 0 <= x <= 1, "x not in range 0..1"
        assert 0 <= y <= 1, "y not in range 0..1"
        assert self.output_width > 0, "Output width must be greater than 0"
        assert self.output_height > 0, "Output height must be greater than 0"
        return {"x": x * self.output_width, "y": y * self.output_height}

    @keyword
    async def get_pointer_position(self) -> Dict[str, float]:
        """Get the current pointer position."""
        return self.pointer_position

    async def connect(self):
        """Connect to the display."""
        if not self.pointer:
            await super().connect()
            await self.move_pointer_to_absolute(self.pointer_position["x"], self.pointer_position["y"])

    async def disconnect(self):
        """Disconnect from the display."""
        if self.pointer:
            await super().disconnect()

    def _close(self):
        """Listener method called when the library goes out of scope."""
        asyncio.get_event_loop().run_until_complete(self.disconnect())
