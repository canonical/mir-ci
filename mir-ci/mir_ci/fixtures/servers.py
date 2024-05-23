import os
import warnings
from collections.abc import Generator
from enum import Flag, auto
from typing import Any, Callable, Mapping, Sequence

from ..program import app
from ..program.display_server import DisplayServer
from . import deb, pip, snap

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
    INPUT_METHOD = auto()
    MIR_SHELL_PROTO = auto()
    ALL = FLOATING_WINDOWS | DRAG_AND_DROP | DISPLAY_CONFIG | SCREENCOPY | INPUT_METHOD | MIR_SHELL_PROTO


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
    mir_ci_server = _mir_ci_server()
    if mir_ci_server is not None and caps in mir_ci_server[0]:
        yield mir_ci_server[1]
    for k, v in _SERVERS:
        if caps in k:
            yield v


def servers(caps: ServerCap = ServerCap.NONE, kwargss: Mapping[Server, Any] = {}) -> Sequence[app.App]:
    """
    Use this in test parametrization to select servers with the necessary capabilities for the
    test in question.

    >>> @pytest.mark.parametrize("server", servers(ServerCap.FLOATING_WINDOWS))
    >>> def test_func(server):
            pass

    >>> @pytest.mark.parametrize(
            "server",
            servers(ServerCap.FLOATING_WINDOWS, {
                ubuntu_frame: {
                    marks=(pytest.mark.skip,)
                }
            })
        )
    >>> def test_func(server):
            pass
    """
    # This tuple has to be realized here, otherwise class-wide parametrization
    # will exhaust the generator on the first test function.
    return tuple(p(**kwargss.get(p, {})) for p in server_params(caps))


def _mir_ci_server():
    """
    Parses the 'MIR_CI_SERVER' environment variable to its corresponding server.
    """
    mir_ci_server = os.environ.get("MIR_CI_SERVER")
    if mir_ci_server is None:
        return

    _MIN_SPLIT_PARTS = 3
    split = mir_ci_server.split(":")
    if len(split) < _MIN_SPLIT_PARTS:
        warnings.warn(f"Too few parts for MIR_CI_SERVER specification: {mir_ci_server}")
        return

    try:
        app_type: app.AppType = app.AppType[split[0]]
    except KeyError:
        error_msg = (
            f"Invalid app type in MIR_CI_SERVER specification: {mir_ci_server}."
            f"Expected 'snap', 'deb' or 'pip' but got {split[0]}"
        )
        warnings.warn(error_msg)
        return

    server_command: str = split[1]
    capability = ServerCap.NONE
    for capability_str in split[2:]:
        try:
            capability = capability | ServerCap[capability_str]
        except KeyError:
            warnings.warn(f"Capability is invalid in MIR_CI_SERVER: {app_type}")
            return

    if app_type == app.AppType.snap:
        return (capability, lambda: snap(server_command))
    elif app_type == app.AppType.pip:
        return (capability, lambda: pip(server_command))
    else:
        return (capability, lambda: deb(server_command))


@server(ServerCap.ALL ^ (ServerCap.FLOATING_WINDOWS | ServerCap.DISPLAY_CONFIG | ServerCap.MIR_SHELL_PROTO))
def ubuntu_frame():
    return snap("ubuntu-frame", channel="22/stable", id="ubuntu_frame")


@server(
    ServerCap.ALL
    ^ (
        ServerCap.FLOATING_WINDOWS
        | ServerCap.DRAG_AND_DROP
        | ServerCap.DISPLAY_CONFIG
        | ServerCap.INPUT_METHOD
        | ServerCap.MIR_SHELL_PROTO
    )
)
def mir_kiosk(*args, id="mir_kiosk", **kwargs):
    return snap("mir-kiosk", *args, id=id, **kwargs)


@server(ServerCap.ALL ^ (ServerCap.DISPLAY_CONFIG | ServerCap.MIR_SHELL_PROTO))
def confined_shell(*args, channel="edge", id="confined_shell", **kwargs):
    return snap("confined-shell", *args, channel=channel, id=id, **kwargs)


@server(ServerCap.ALL ^ ServerCap.DISPLAY_CONFIG)
def mir_test_tools(*args, channel="24/beta", cmd=("mir-test-tools.demo-server",), id="mir_test_tools", **kwargs):
    return snap("mir-test-tools", channel=channel, cmd=(*cmd, *args), id=id, **kwargs)


@server(ServerCap.ALL ^ ServerCap.MIR_SHELL_PROTO)
def mir_demo_server(*args, debs=("mir-test-tools", "mir-graphics-drivers-desktop"), id="mir_demo_server", **kwargs):
    return deb("mir_demo_server", *args, debs=debs, id=id, **kwargs)


@server(ServerCap.ALL ^ ServerCap.MIR_SHELL_PROTO)
def miriway(*args, channel="stable", classic=True, **kwargs):
    return snap("miriway", *args, channel=channel, classic=classic, **kwargs)


@server(
    ServerCap.ALL
    ^ (ServerCap.DISPLAY_CONFIG | ServerCap.SCREENCOPY | ServerCap.INPUT_METHOD | ServerCap.MIR_SHELL_PROTO)
)
def gnome_shell(
    *args,
    cmd=("gnome-shell", "--wayland", "--no-x11", "--wayland-display", DisplayServer.get_wayland_display()),
    id="gnome_shell",
    **kwargs,
):
    return deb("gnome-shell", *args, cmd=(*cmd, *args), id=id, **kwargs)
