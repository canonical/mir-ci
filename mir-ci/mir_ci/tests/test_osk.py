import itertools
from pathlib import Path
from typing import Collection

import pytest
from mir_ci import VARIANT
from mir_ci.fixtures import apps, servers
from mir_ci.program.app import App
from mir_ci.program.display_server import DisplayServer
from mir_ci.program.program import ProgramError
from mir_ci.wayland.screencopy_tracker import ScreencopyTracker
from mir_ci.wayland.virtual_pointer import VirtualPointer

ROBOT_PATH = Path(__file__).parent / "robot"


def collect_asset(asset: Path, variant):
    variants = reversed((variant, *variant.parents[:-1]))
    return itertools.chain(
        asset.glob("*"),
        *((asset / "variants" / v).glob("*") for v in variants),
    )


def collect_assets(platform: str, resources: Collection[str], suite: str, variant: Path = VARIANT):
    return {
        p.name: p
        for p in itertools.chain(
            collect_asset(ROBOT_PATH / "platforms" / platform, variant),
            *(collect_asset(ROBOT_PATH / "resources" / resource, variant) for resource in resources),
            collect_asset(ROBOT_PATH / "suites" / suite, variant),
        )
        if p.is_file()
    }


@pytest.mark.deps(
    pip_pkgs=(
        ("robotframework~=6.1.1", "robot"),
        ("rpaframework", "RPA"),
        ("rpaframework-recognition", "RPA.recognition"),
    ),
)
@pytest.mark.parametrize(
    "server",
    servers.servers(
        servers.ServerCap.INPUT_METHOD,
        {
            servers.confined_shell: {
                "marks": (pytest.mark.xfail(reason="OSK not activating", raises=ProgramError, strict=True),)
            },
            servers.miriway: {
                "marks": (pytest.mark.xfail(reason="OSK not activating", raises=ProgramError, strict=True),)
            },
        },
    ),
)
@pytest.mark.parametrize("osk", (apps.ubuntu_frame_osk(),))
@pytest.mark.parametrize("app", (apps.pluma(),))
class TestOSK:
    async def test_osk_typing(self, server, osk, app, tmp_path):
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions + osk.extensions
        server_instance = DisplayServer(
            server,
            add_extensions=extensions,
        )
        assets = collect_assets("wayland", ("kvm", "osk"), "osk")

        async with server_instance, server_instance.program(app) as app, server_instance.program(osk) as osk:
            tuple((tmp_path / k).symlink_to(v) for k, v in assets.items())
            robot = server_instance.program(App(("robot", "-d", tmp_path, tmp_path)))
            async with robot:
                await robot.wait(120)
