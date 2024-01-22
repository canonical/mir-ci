import asyncio

from robot.api.deco import keyword, library

from mir_ci import apps
from mir_ci.display_server import DisplayServer
from mir_ci.program import Program
from mir_ci.virtual_pointer import Button, VirtualPointer

@library(scope='TEST')
class DragAndDrop:
    def __init__(self) -> None:
        self._actions = []
        self._app_command = None
        self._pointer = None
        self._program = None
        self._server = None
        self._server_command = None

    @keyword
    def run_async(self, server_name : str, app_command : str, flush : bool = True) -> None:
        self._server_command = getattr(apps, server_name)().values[0]
        self._app_command = tuple(app_command.split())

        if self._actions:
            asyncio.run(self.start_async())
            if flush:
                self._actions = []

    @keyword
    def sleep_for(self, time : float):
        self.register_action(lambda _: asyncio.sleep(time), should_await = True)

    @keyword
    def move_pointer_to_absolute(self, x : float, y : float):
        self.register_action(lambda self: self.pointer.move_to_absolute(x, y))

    @keyword
    def press_left_button(self):
        self.register_action(lambda self: self.pointer.button(Button.LEFT, True))

    @keyword
    def release_left_button(self):
        self.register_action(lambda self: self.pointer.button(Button.LEFT, False))

    @keyword
    def wait_program(self):
        self.register_action(lambda self: self.program.wait(), should_await = True)

    @keyword
    def kill_program(self):
        self.register_action(lambda self: self.program.kill(), should_await = True)

    @keyword
    def assert_program_is_running(self):
        self.register_action(lambda self: self.assert_helper(self.program.is_running(),
                                                             "Program should be running!"))
    @keyword
    def program_output(self):
        return self.program.output

    @property
    def pointer(self) -> VirtualPointer:
        if not self._pointer:
            raise SystemError('Pointer not found!')
        return self._pointer

    @property
    def program(self) -> Program:
        if not self._program:
            raise SystemError('Program not found!')
        return self._program

    @staticmethod
    def assert_helper(condition, error_message : str = ''):
        assert condition, f'Assertion failed! {error_message}'

    def register_action(self, action, should_await = False):
        self._actions.append((action, should_await))

    async def start_async(self):
        self._server = DisplayServer(self._server_command, add_extensions=VirtualPointer.required_extensions)
        self._pointer = VirtualPointer(self._server.display_name)
        self._program = self._server.program(apps.App(self._app_command))

        async with self._server, self._program, self._pointer:
            for action, should_await in self._actions:
                if should_await:
                    await action(self)
                else:
                    action(self)
