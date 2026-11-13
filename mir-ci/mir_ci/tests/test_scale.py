import asyncio
import itertools
from pathlib import Path
from textwrap import dedent
from typing import Collection

import pytest
from mir_ci import VARIANT
from mir_ci.fixtures.servers import ServerCap, servers
from mir_ci.program.app import App, AppType
from mir_ci.program.display_server import DisplayServer
from mir_ci.wayland.output_watcher import OutputWatcher

TESTS_PATH = Path(__file__).parent
APP_PATH = "gtk4-demo"
ROBOT_PATH = TESTS_PATH / "robot"


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


@pytest.mark.xdg(
    XDG_CONFIG_HOME={
        "glib-2.0/settings/keyfile": dedent("""\
            [org/gnome/desktop/interface]
            color-scheme='prefer-light'
            gtk-theme='Adwaita'
            icon-theme='Adwaita'
            font-name='Ubuntu 11'
            cursor-theme='Adwaita'
            cursor-size=24
            font-antialiasing='grayscale'
        """),
    },
)
@pytest.mark.env(GSETTINGS_BACKEND="keyfile")
@pytest.mark.parametrize("server", servers(ServerCap.DISPLAY_CONFIG))
@pytest.mark.parametrize("scale", [1.0, 1.5, 2.0])
@pytest.mark.deps(
    debs=(
        "libgirepository-2.0-dev",
        "gtk-4-examples",
    ),
    pip_pkgs=(
        ("pygobject", "gi"),
        ("robotframework~=6.1.1", "robot"),
        ("rpaframework", "RPA"),
        ("rpaframework-recognition", "RPA.recognition"),
    ),
)
class TestScale:
    async def test_scale(self, robot_log, server, scale, tmp_path) -> None:
        extensions = ("all",)  # TODO no need to enable all extension

        server_instance = DisplayServer(
            server,
            add_extensions=extensions,
            env={"MIR_SERVER_X11_OUTPUT": "1024x768", "MIR_SERVER_DISPLAY_SCALE": str(scale)},
        )
        output_watcher = OutputWatcher(server_instance.display_name)

        async with server_instance, output_watcher, server_instance.program(App(APP_PATH, AppType.deb)):
            await asyncio.wait_for(output_watcher.wait_done(), timeout=5.0)
            assert output_watcher.mode is not None, "Failed to get output mode from compositor"

            assets = collect_assets(
                "wayland", ("kvm", "osk"), "scale", VARIANT / "{0}/{0}x{1}".format(*output_watcher.mode)
            )
            tuple((tmp_path / k).symlink_to(v) for k, v in assets.items())
            robot = server_instance.program(
                App(("robot", "-d", tmp_path, "--log", robot_log, "--variable", f"SCALE:{scale}", tmp_path))
            )

            async with robot:
                await robot.wait(120)
