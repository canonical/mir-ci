from display_server import DisplayServer
from pathlib import Path
import pytest
import os
import re
import asyncio
import apps

try:
    from virtual_pointer import VirtualPointer, Button
except ModuleNotFoundError as e:
    pass

APP_PATH = Path(__file__).parent / 'clients' / 'drag_and_drop_demo.py'

class TestDragAndDrop:
    @pytest.mark.parametrize('app', [
        ('python3', str(APP_PATH), '--source', 'pixbuf', '--target', 'pixbuf', '--expect', 'pixbuf'),
        ('python3', str(APP_PATH), '--source', 'text', '--target', 'text', '--expect', 'text'),
    ])
    async def test_source_and_dest_match(self, server, app) -> None:
        server = DisplayServer(server, add_extensions=VirtualPointer.required_extensions)
        pointer = VirtualPointer(server.display_name)
        program = server.program(app)

        async with server, program, pointer:
            await asyncio.sleep(1)
            pointer.move_to_absolute(40, 40)
            await asyncio.sleep(1)
            pointer.button(Button.LEFT, True)
            await asyncio.sleep(1)
            pointer.move_to_absolute(120, 70)
            await asyncio.sleep(1)
            pointer.move_to_absolute(200, 100)
            await asyncio.sleep(1)
            pointer.button(Button.LEFT, False)
            await program.wait()

        assert program.process.returncode == 0