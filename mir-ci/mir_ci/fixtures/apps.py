import pytest

from . import deb, snap


def qterminal(*args: str, debs=("qterminal", "qtwayland5"), marks=(), **kwargs):
    marks = (pytest.mark.xdg(XDG_CONFIG_HOME={"qterminal.org/qterminal.ini": "[General]\nAskOnExit=false"}), *marks)
    return deb("qterminal", *args, debs=debs, marks=marks, **kwargs)


def pluma(*args: str, **kwargs):
    return deb("pluma", *args, **kwargs)


def wpe(*args: str, cmd=(), **kwargs):
    return snap("wpe-webkit-mir-kiosk", cmd=cmd or ("wpe-webkit-mir-kiosk.cog", *args), **kwargs)


def ubuntu_frame_osk(marks=(), **kwargs):
    marks = (pytest.mark.xdg(XDG_CONFIG_HOME={}), *marks)
    return snap(
        "ubuntu-frame-osk",
        channel="22/stable",
        marks=marks,
        extensions=("zwlr_layer_shell_v1", "zwp_virtual_keyboard_manager_v1", "zwp_virtual_keyboard_manager_v1"),
        **kwargs,
    )
