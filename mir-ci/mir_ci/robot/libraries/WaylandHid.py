from robot.api.deco import keyword, library
from mir_ci.virtual_pointer import VirtualPointer, Button


@library(scope='TEST')
class WaylandHid(VirtualPointer):

    @keyword
    def move_pointer_to_absolute(self, x: float, y: float) -> None:
        self.move_to_absolute(x, y)

    @keyword
    def move_pointer_to_proportional(self, x: float, y: float) -> None:
        self.move_to_proportional(x, y)

    @keyword("Press ${button} Button")
    def press_pointer_button(self, button: str) -> None:
        self.button(Button[button], True)

    @keyword("Release ${button} Button")
    def release_pointer_button(self, button: str) -> None:
        self.button(Button[button], False)

    @keyword
    async def connect(self):
        await self.__aenter__()  # pylint: disable=unnecessary-dunder-call

    @keyword
    async def disconnect(self):
        await self.__aexit__()
