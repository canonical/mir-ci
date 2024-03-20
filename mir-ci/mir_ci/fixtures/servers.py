from enum import Flag, auto
from typing import Callable, Sequence

from ..program import app
from . import deb, snap

Server = Callable[[], app.App]


class ServerCap(Flag):
    """
    Server capabilities for test parametrization, see servers() documentation.
    """

    NONE = 0
    FLOATING_WINDOWS = auto()
    DRAG_AND_DROP = auto()
    ALL = FLOATING_WINDOWS | DRAG_AND_DROP


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
    return tuple(v() for k, v in _SERVERS if caps in k)


@server(ServerCap.ALL ^ ServerCap.FLOATING_WINDOWS)
def ubuntu_frame():
    return snap("ubuntu-frame", channel="22/stable", id="ubuntu_frame")


@server(ServerCap.ALL ^ (ServerCap.FLOATING_WINDOWS | ServerCap.DRAG_AND_DROP))
def mir_kiosk():
    return snap("mir-kiosk", id="mir_kiosk")


@server
def confined_shell():
    return snap("confined-shell", channel="edge", id="confined_shell")


@server
def mir_test_tools():
    return snap("mir-test-tools", channel="22/beta", cmd=("mir-test-tools.demo-server",), id="mir_test_tools")


@server
def mir_demo_server():
    return deb("mir_demo_server", debs=("mir-test-tools", "mir-graphics-drivers-desktop"), id="mir_demo_server")
