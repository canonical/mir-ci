import asyncio
import os

from robot.api.deco import keyword, library
from robot.api.exceptions import FatalError
from mir_ci.virtual_pointer import VirtualPointer, Button


@library(scope='TEST', listener='SELF')
class WaylandHid(VirtualPointer):
    def __init__(self) -> None:
        display_name = os.environ.get("WAYLAND_DISPLAY")
        if display_name is None:
            raise FatalError("WAYLAND_DISPLAY is not defined.")
        if not display_name:
            display_name = "wayland-0"

        super().__init__(display_name)

    @keyword
    async def move_pointer_to_absolute(self, x: float, y: float) -> None:
        await self.connect()
        self.move_to_absolute(x, y)

    @keyword
    async def move_pointer_to_proportional(self, x: float, y: float) -> None:
        await self.connect()
        self.move_to_proportional(x, y)

    @keyword("Press ${button} Button")
    async def press_pointer_button(self, button: str) -> None:
        await self.connect()
        self.button(Button[button], True)

    @keyword("Release ${button} Button")
    async def release_pointer_button(self, button: str) -> None:
        await self.connect()
        self.button(Button[button], False)

    async def connect(self):
        if not self.pointer:
            await self.__aenter__()  # pylint: disable=unnecessary-dunder-call

    def _end_test(self, data, result):  # pylint: disable=unused-argument
        asyncio.get_event_loop().run_until_complete(self.__aexit__())
