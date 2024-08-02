import itertools
from pathlib import Path
from textwrap import dedent
from typing import Collection

import pytest
from mir_ci import VARIANT
from mir_ci.fixtures.servers import ServerCap, servers
from mir_ci.program.app import App, AppType
# from mir_ci.program.display_server import DisplayServer

from display_server_static_file import DisplayServerStaticFile

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

def get_display_config(scale: float) -> dict:
    return {
        "layouts": {
            "default": {
                "cards": [
                    {
                        "card-id": 0,
                        "unknown-1": {
                            "state": "enabled",
                            "mode": "1280x1024@60",
                            "position": [
                                0,
                                0
                            ],
                            "orientation": "normal",
                            "scale": scale,
                            "group": 0
                        }
                    }
                ]
            }
        }
    }

@pytest.mark.xdg(
    XDG_CONFIG_HOME={
        "glib-2.0/settings/keyfile": dedent(
            """\
            [org/gnome/desktop/interface]
            color-scheme='prefer-light'
            gtk-theme='Adwaita'
            icon-theme='Adwaita'
            font-name='Ubuntu 11'
            cursor-theme='Adwaita'
            cursor-size=24
            font-antialiasing='grayscale'
        """
        ),
    },
)
@pytest.mark.env(GSETTINGS_BACKEND="keyfile")
@pytest.mark.parametrize("server", servers(ServerCap.FLOATING_WINDOWS | ServerCap.DISPLAY_CONFIG))
@pytest.mark.parametrize("scale", [1.0, 1.25, 1.5, 1.75, 2.0])
@pytest.mark.deps(
    debs=(
        "gtk-4-examples",
    ),
    pip_pkgs=(
        ("pygobject", "gi"),
        ("robotframework~=6.1.1", "robot"),
        ("rpaframework", "RPA"),
        ("rpaframework-recognition", "RPA.recognition"),
    ),
)
class TestFractionalScaleV1:
    async def test_fractional_scale_v1(self, robot_log, server, scale, tmp_path) -> None:
        extensions = ('all',)  # TODO no need to enable all extension
        display_config = get_display_config(scale)

        server_instance = DisplayServerStaticFile(server, add_extensions=extensions)
        server_instance.write_config(display_config)

        assets = collect_assets("wayland", ["kvm"], "fractional_scale_v1")

        async with server_instance, server_instance.server.program(App(APP_PATH, AppType.deb)):
            tuple((tmp_path / k).symlink_to(v) for k, v in assets.items())

            robot = server_instance.server.program(
                    App(("robot", "-d", tmp_path, "--log", robot_log, "--variable", f"SCALE:{scale}", tmp_path)))

            async with robot:
                await robot.wait(120)
