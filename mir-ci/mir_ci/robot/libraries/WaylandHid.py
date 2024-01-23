import asyncio

from robot.api.deco import keyword, library
from mir_ci.virtual_pointer import VirtualPointer, Button


@library(scope='TEST', listener='SELF')
class WaylandHid(VirtualPointer):

    def __init__(self, display_name: str) -> None:
        super().__init__(display_name)
        self.event_loop = None

    @keyword()
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
        if self.pointer:
            return
        await self.__aenter__()  # pylint: disable=unnecessary-dunder-call
        self.event_loop = asyncio.get_event_loop()

    def _end_test(self, data, result):
        _ = (data, result)
        self.event_loop.run_until_complete(self.__aexit__())
