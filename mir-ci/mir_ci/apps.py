import pytest

from typing import Any, Optional, Union, Collection, Literal

AppType = Literal["snap", "deb", "pip"]


class App:
    command: Collection[str]
    app_type: Optional[AppType]

    def __init__(self, command: Collection[str], app_type: Optional[AppType] = None) -> None:
        self.command = command
        self.app_type = app_type


def _dependency(
    cmd: Collection[str],
    app_type: AppType,
    snap: Optional[str] = None,
    channel: str = "latest/stable",
    debs: Collection[str] = (),
    pip_pkgs: Collection[str] = (),
    marks: Union[pytest.MarkDecorator, Collection[Union[pytest.MarkDecorator, pytest.Mark]]] = (),
    id: Optional[str] = None,
    extra: Any = None,
):
    if isinstance(marks, pytest.Mark):
        marks = (marks,)

    ret = cmd
    if extra is not None:
        ret = (ret, extra)

    return pytest.param(
        App(ret, app_type),
        marks=(  # type: ignore
            pytest.mark.deps(cmd=cmd, snap=snap, debs=debs, pip_pkgs=pip_pkgs, channel=channel, app_type=app_type),
            *marks,
        ),
        id=id,
    )


def snap(snap: str, *args: str, cmd: Collection[str] = (), id=None, **kwargs):
    return _dependency(cmd=cmd or (snap, *args), app_type="snap", snap=snap, id=id or snap, **kwargs)


def deb(
    deb: str, *args: str, cmd: Collection[str] = (), debs: Collection[str] = (), id: Optional[str] = None, **kwargs
):
    return _dependency(cmd=cmd or (deb, *args), app_type="deb", debs=debs or (deb,), id=id or deb, **kwargs)


def pip(pkg: str, *args: str, cmd: Collection[str] = (), id: Optional[str] = None, **kwargs):
    return _dependency(
        pip_pkgs=(pkg,), app_type="pip", cmd=cmd or ("python3", "-m", pkg, *args), id=id or pkg, **kwargs
    )


def qterminal(*args: str, debs: Collection[str] = ("qterminal", "qtwayland5"), marks=(), **kwargs):
    marks = (pytest.mark.xdg(XDG_CONFIG_HOME={"qterminal.org/qterminal.ini": "[General]\nAskOnExit=false"}), *marks)
    return deb("qterminal", *args, debs=debs, marks=marks, **kwargs)


def pluma(*args: str, **kwargs):
    return deb("pluma", *args, **kwargs)


def wpe(*args: str, cmd: Collection[str] = (), **kwargs):
    return snap("wpe-webkit-mir-kiosk", cmd=cmd or ("wpe-webkit-mir-kiosk.cog", *args), **kwargs)


def ubuntu_frame():
    return snap("ubuntu-frame", channel="22/stable", id="ubuntu_frame")


def mir_kiosk():
    return snap("mir-kiosk", id="mir_kiosk")


def confined_shell():
    return snap("confined-shell", channel="edge", id="confined_shell")


def mir_test_tools():
    return snap("mir-test-tools", channel="22/beta", cmd=("mir-test-tools.demo-server",), id="mir_test_tools")


def mir_demo_server():
    return deb("mir_demo_server", debs=("mir-test-tools", "mir-graphics-drivers-desktop"), id="mir_demo_server")
