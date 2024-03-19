import itertools
from pathlib import Path
from typing import Collection

import pytest
from mir_ci import VARIANT
from mir_ci.fixtures import apps
from mir_ci.program.display_server import DisplayServer
from mir_ci.wayland.screencopy_tracker import ScreencopyTracker
from mir_ci.wayland.virtual_pointer import VirtualPointer

ROBOT_PATH = Path(__file__).parent / "robot"


def collect_asset(asset: Path, variant):
    variants = (variant, *variant.parents[:-1])
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
    }


@pytest.mark.parametrize(
    "modern_server",
    (
        apps.mir_demo_server(),
        apps.mir_test_tools(),
        apps.ubuntu_frame(),
    ),
)
@pytest.mark.parametrize("osk", (apps.ubuntu_frame_osk(),))
@pytest.mark.parametrize("app", (apps.pluma(),))
class TestOSK:
    async def test_osk_typing(self, modern_server, osk, app, tmp_path):
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions
        server_instance = DisplayServer(
            modern_server,
            add_extensions=extensions,
        )

        robot = server_instance.program(apps.App(("robot", "-d", tmp_path, tmp_path)))

        assets = collect_assets("wayland", ("osk",), "osk")

        tuple((tmp_path / k).symlink_to(v) for k, v in assets.items())

        async with server_instance, server_instance.program(app) as app, server_instance.program(osk) as osk, robot:
            await robot.wait(120)
            await osk.kill()
            await app.kill()
