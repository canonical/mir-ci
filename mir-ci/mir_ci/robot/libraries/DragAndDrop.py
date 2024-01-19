import asyncio

from robot.api.deco import not_keyword

from mir_ci import apps
from mir_ci.display_server import DisplayServer
from mir_ci.virtual_pointer import Button, VirtualPointer

class DragAndDrop:
    ROBOT_LIBRARY_SCOPE = 'TEST'

    def __init__(self) -> None:
        self._actions = []
        self._command = None
        self._pointer = None
        self._program = None
        self._server = None
        self._server_cmd = None

    def run_async(self, server_name : str, app_command : str):
        self._server_cmd = getattr(apps, server_name)().values[0]
        self._command = tuple(app_command.split())

        if self._actions:
            asyncio.run(self.start_async())
            self._actions = []

    def sleep_for(self, time : float):
        self.register_action(lambda _: asyncio.sleep(time), should_await = True)

    def move_pointer_to_absolute(self, x : float, y : float):
        self.register_action(lambda context: context.pointer.move_to_absolute(x, y))

    def press_left_button(self):
        self.register_action(lambda context: context.pointer.button(Button.LEFT, True))

    def release_left_button(self):
        self.register_action(lambda context: context.pointer.button(Button.LEFT, False))

    def wait_program(self):
        self.register_action(lambda context: context.program.wait(), should_await = True)

    def kill_program(self):
        self.register_action(lambda context: context.program.kill(), should_await = True)

    def assert_program_is_running(self):
        self.register_action(lambda context: DragAndDrop.assert_helper(context.program.is_running(),
                                                                       "Program should be running!"))

    def program_output(self):
        return self.program.output

    @property
    def pointer(self):
        if not self._pointer:
            raise SystemError('Pointer not found!')
        return self._pointer

    @property
    def program(self):
        if not self._program:
            raise SystemError('Program not found!')
        return self._program

    @staticmethod
    @not_keyword
    def assert_helper(condition, error_message : str = ''):
        assert condition, 'Assertion failed! ' + error_message

    @not_keyword
    def register_action(self, action, should_await = False):
        self._actions.append((action, should_await))

    @not_keyword
    async def start_async(self):
        self._server = DisplayServer(self._server_cmd, add_extensions=VirtualPointer.required_extensions)
        self._pointer = VirtualPointer(self._server.display_name)
        self._program = self._server.program(apps.App(self._command))

        async with self._server, self._program, self._pointer:
            for action, should_await in self._actions:
                if should_await:
                    await action(self)
                else:
                    action(self)
