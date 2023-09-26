from mir_ci import SLOWDOWN
from mir_ci.display_server import DisplayServer
from pathlib import Path
import pytest
import os
import re
import asyncio
from mir_ci import apps

from mir_ci.virtual_pointer import VirtualPointer, Button

APP_PATH = Path(__file__).parent / 'clients' / 'drag_and_drop_demo.py'
STARTUP_TIME=1.5 * SLOWDOWN
A_SHORT_TIME=0.3

@pytest.mark.parametrize('modern_server', [
    apps.ubuntu_frame(),
    # apps.mir_kiosk(), we need servers based on Mir 2.14 or later
    apps.confined_shell(),
    apps.mir_test_tools(),
    apps.mir_demo_server(),
])
class TestDragAndDrop:
    @pytest.mark.parametrize('app', [
        ('python3', str(APP_PATH), '--source', 'pixbuf', '--target', 'pixbuf', '--expect', 'pixbuf'),
        ('python3', str(APP_PATH), '--source', 'text', '--target', 'text', '--expect', 'text'),
    ])
    @pytest.mark.deps(debs=('libgtk-4-dev',), pip_pkgs=(('pygobject', 'gi'),))
    async def test_source_and_dest_match(self, modern_server, app) -> None:
        modern_server = DisplayServer(modern_server, add_extensions=VirtualPointer.required_extensions)
        pointer = VirtualPointer(modern_server.display_name)
        program = modern_server.program(app)

        async with modern_server, program, pointer:
            await asyncio.sleep(STARTUP_TIME)
            pointer.move_to_absolute(40, 40)
            await asyncio.sleep(A_SHORT_TIME)
            pointer.button(Button.LEFT, True)
            await asyncio.sleep(A_SHORT_TIME)
            pointer.move_to_absolute(120, 70)
            await asyncio.sleep(A_SHORT_TIME)
            pointer.move_to_absolute(200, 100)
            await asyncio.sleep(A_SHORT_TIME)
            pointer.button(Button.LEFT, False)
            await program.wait()

    @pytest.mark.parametrize('app', [
        ('python3', str(APP_PATH), '--source', 'pixbuf', '--target', 'text', '--expect', 'pixbuf'),
        ('python3', str(APP_PATH), '--source', 'text', '--target', 'pixbuf', '--expect', 'text'),
        ('python3', str(APP_PATH), '--source', 'pixbuf', '--target', 'text', '--expect', 'text'),
        ('python3', str(APP_PATH), '--source', 'text', '--target', 'pixbuf', '--expect', 'pixbuf'),
    ])
    @pytest.mark.deps(debs=('libgtk-4-dev',), pip_pkgs=(('pygobject', 'gi'),))
    async def test_source_and_dest_mismatch(self, modern_server, app) -> None:
        modern_server = DisplayServer(modern_server, add_extensions=VirtualPointer.required_extensions)
        pointer = VirtualPointer(modern_server.display_name)
        program = modern_server.program(app)

        async with modern_server, program, pointer:
            await asyncio.sleep(STARTUP_TIME)
            pointer.move_to_absolute(40, 40)
            await asyncio.sleep(A_SHORT_TIME)
            pointer.button(Button.LEFT, True)
            await asyncio.sleep(A_SHORT_TIME)
            pointer.move_to_absolute(120, 70)
            await asyncio.sleep(A_SHORT_TIME)
            pointer.move_to_absolute(200, 100)
            await asyncio.sleep(A_SHORT_TIME)
            pointer.button(Button.LEFT, False)
            await asyncio.sleep(A_SHORT_TIME)
            assert program.is_running()
            await program.kill()
