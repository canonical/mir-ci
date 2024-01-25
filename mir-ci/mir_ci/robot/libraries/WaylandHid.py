import asyncio
import os

from mir_ci.virtual_pointer import Button, VirtualPointer
from robot.api.deco import keyword, library


@library(scope="TEST", listener="SELF")
class WaylandHid(VirtualPointer):
    """
    A Robot Framework library for interacting with virtual Wayland-based HIDs.

    The client connects to the display upon entering the first keyword,
    and disconnects when the test case ends.

    If WAYLAND_DISPLAY is not defined, it defaults to 'wayland-0'.
    """

    def __init__(self) -> None:
        display_name = os.environ.get("WAYLAND_DISPLAY", "wayland-0")
        super().__init__(display_name)

    @keyword
    async def move_pointer_to_absolute(self, x: float, y: float) -> None:
        """Move the virtual pointer to an absolute position within the output."""
        await self.connect()
        self.move_to_absolute(x, y)

    @keyword
    async def move_pointer_to_proportional(self, x: float, y: float) -> None:
        """Move the virtual pointer to a position proportional to the size of the output."""
        await self.connect()
        self.move_to_proportional(x, y)

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

    async def connect(self):
        """Connect to the display."""
        if not self.pointer:
            await super().connect()

    async def disconnect(self):
        """Disconnect from the display."""
        if self.pointer:
            await super().disconnect()

    def _end_test(self, data, result):  # pylint: disable=unused-argument
        """Listener method called at the end of the test case."""
        asyncio.get_event_loop().run_until_complete(self.disconnect())
