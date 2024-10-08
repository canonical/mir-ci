import itertools
import os
from importlib import import_module
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
    "platform",
    (
        "wayland",
        pytest.param(
            "zapper",
            marks=(
                pytest.mark.zapper,
                pytest.mark.skipif("ZAPPER_HOST" not in os.environ, reason="ZAPPER_HOST unset"),
                pytest.mark.deps(
                    pip_pkgs=(
                        (
                            "git+https://github.com/canonical/checkbox.git#subdirectory=checkbox-support",
                            "checkbox-support",
                        ),
                        ("git+https://github.com/canonical/checkbox.git#subdirectory=checkbox-ng", "plainbox"),
                    )
                ),
            ),
        ),
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
    async def test_osk_typing(self, robot_log, platform, server, osk, app, tmp_path):
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions + osk.extensions
        server_instance = DisplayServer(
            server,
            add_extensions=extensions,
        )
        assets = collect_assets(platform, ("kvm", "osk"), "osk")

        async with server_instance, server_instance.program(app) as app, server_instance.program(osk) as osk:
            if platform == "wayland":
                tuple((tmp_path / k).symlink_to(v) for k, v in assets.items())
                robot = server_instance.program(App(("robot", "-d", tmp_path, "--log", robot_log, tmp_path)))
                async with robot:
                    await robot.wait(120)

            elif platform == "zapper":
                proxy = import_module("checkbox_support.scripts.zapper_proxy")
                procedure = b""
                asset_map = {}
                for name, path in assets.items():
                    with open(path, "rb") as f:
                        # TODO: we're sending the whole robot suite as bytes, as Zapper
                        # doesn't currently support "running" a folder.
                        if path.suffix == ".robot":
                            procedure += f.read() + b"\n\n"
                        else:
                            asset_map[name] = f.read()

                status, log = proxy.zapper_run(os.environ["ZAPPER_HOST"], "robot_run", procedure, asset_map, {})

                with open(robot_log.is_absolute() and robot_log or (tmp_path / robot_log), "w") as f:
                    f.write(log)

                if not status:
                    pytest.fail("Robot run failed")
