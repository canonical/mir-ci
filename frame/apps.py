import pytest

from typing import Any, Optional, Union, Collection

def snap(
        snap: str,
        *args: str,
        channel: str = 'latest/stable',
        cmd: Collection[str] = (),
        marks: Union[pytest.MarkDecorator, Collection[Union[pytest.MarkDecorator, pytest.Mark]]] = (),
        id: Optional[str] = None,
        extra: Any = None):

    if isinstance(marks, pytest.Mark):
        marks = (marks,)

    ret = cmd or (snap, *args)
    if extra is not None:
        ret = (ret, extra)

    return pytest.param(
        ret,
        marks=(                             # type: ignore
            pytest.mark.deps(
                cmd=cmd or (snap, *args),
                snap=snap,
                channel=channel),
            *marks),
        id=id or snap)

def deb(
        deb: str,
        *args: str,
        cmd: Collection[str] = (),
        debs: Collection[str] = (),
        marks: Union[pytest.MarkDecorator, Collection[Union[pytest.MarkDecorator, pytest.Mark]]] = (),
        id: Optional[str] = None,
        extra: Any = None):

    if isinstance(marks, pytest.Mark):
        marks = (marks,)

    ret = cmd or (deb, *args)
    if extra is not None:
        ret = (ret, extra)

    return pytest.param(
        ret,
        marks=(                             # type: ignore
            pytest.mark.deps(
                cmd=cmd or (deb, *args),
                debs=debs or (deb,)),
            *marks),
        id=id or deb)

def qterminal(*args: str, debs: Collection[str] = ('qterminal', 'qtwayland5'), marks=(), **kwargs):
    marks = (
        pytest.mark.xdg(XDG_CONFIG_HOME={'qterminal.org/qterminal.ini': '[General]\nAskOnExit=false'}),
        *marks)
    return deb('qterminal', *args, debs=debs, marks=marks, **kwargs)

def gedit(*args: str, **kwargs):
    return deb('gedit', '-s', *args, **kwargs)

def wpe(*args: str, cmd: Collection[str] = (), **kwargs):
    return snap('wpe-webkit-mir-kiosk', cmd=cmd or ('wpe-webkit-mir-kiosk.cog', *args), **kwargs)
