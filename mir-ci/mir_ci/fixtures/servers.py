from collections.abc import Generator
from enum import Flag, auto
from typing import Callable, Sequence

from ..program import app
from ..program.display_server import DisplayServer
from . import deb, snap

Server = Callable[[], app.App]


class ServerCap(Flag):
    """
    Server capabilities for test parametrization, see servers() documentation.
    """

    NONE = 0
    FLOATING_WINDOWS = auto()
    DRAG_AND_DROP = auto()
    DISPLAY_CONFIG = auto()
    SCREENCOPY = auto()
    ALL = FLOATING_WINDOWS | DRAG_AND_DROP | DISPLAY_CONFIG | SCREENCOPY


_SERVERS: set[tuple[ServerCap, Server]] = set()


def server(arg: ServerCap | Server):
    if isinstance(arg, ServerCap):

        def _wrap(func):
            _SERVERS.add((arg, func))
            return func

        return _wrap
    else:
        _SERVERS.add((ServerCap.ALL, arg))
        return arg


def server_params(caps: ServerCap = ServerCap.NONE) -> Generator[Server, None, None]:
    """
    Use this in fixture parametrization to select servers with the necessary capabilities
    for the fixture in question.

    >>> @pytest.fixture(params=server_params(ServerCap.DRAG_AND_DROP))
    >>> def func(request) -> app.App:
            return request.param()
    """
    return (v for k, v in _SERVERS if caps in k)


def servers(caps: ServerCap = ServerCap.NONE) -> Sequence[app.App]:
    """
    Use this in test parametrization to select servers with the necessary capabilities for the
    test in question.

    >>> @pytest.mark.parametrize("server", servers(ServerCap.FLOATING_WINDOWS))
    >>> def test_func(server):
            pass
    """
    # This tuple has to be realized here, otherwise class-wide parametrization
    # will exhaust the generator on the first test function.
    return tuple(p() for p in server_params(caps))


@server(ServerCap.ALL ^ (ServerCap.FLOATING_WINDOWS | ServerCap.DISPLAY_CONFIG))
def ubuntu_frame():
    return snap("ubuntu-frame", channel="22/stable", id="ubuntu_frame")


@server(ServerCap.ALL ^ (ServerCap.FLOATING_WINDOWS | ServerCap.DRAG_AND_DROP | ServerCap.DISPLAY_CONFIG))
def mir_kiosk():
    return snap("mir-kiosk", id="mir_kiosk")


@server(ServerCap.ALL ^ ServerCap.DISPLAY_CONFIG)
def confined_shell():
    return snap("confined-shell", channel="edge", id="confined_shell")


@server(ServerCap.ALL ^ ServerCap.DISPLAY_CONFIG)
def mir_test_tools():
    return snap("mir-test-tools", channel="22/beta", cmd=("mir-test-tools.demo-server",), id="mir_test_tools")


@server
def mir_demo_server():
    return deb("mir_demo_server", debs=("mir-test-tools", "mir-graphics-drivers-desktop"), id="mir_demo_server")


@server
def miriway():
    return snap("miriway", channel="stable", classic=True)


@server(ServerCap.ALL ^ (ServerCap.DISPLAY_CONFIG | ServerCap.SCREENCOPY))
def gnome_shell():
    return deb(
        "gnome-shell",
        "--wayland",
        "--no-x11",
        "--wayland-display",
        DisplayServer.get_wayland_display(),
        id="gnome_shell",
    )
