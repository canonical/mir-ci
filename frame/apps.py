import pytest

from typing import Any, Optional, Union, Collection

def _dependency(
        cmd: Collection[str],
        snap: Optional[str] = None,
        channel: str = 'latest/stable',
        debs: Collection[str] = (),
        pip_pkgs: Collection[str] = (),
        marks: Union[pytest.MarkDecorator, Collection[Union[pytest.MarkDecorator, pytest.Mark]]] = (),
        id: Optional[str] = None,
        extra: Any = None):

    if isinstance(marks, pytest.Mark):
        marks = (marks,)

    ret = cmd
    if extra is not None:
        ret = (ret, extra)

    return pytest.param(
        ret,
        marks=(                             # type: ignore
            pytest.mark.deps(
                cmd=cmd,
                snap=snap,
                debs=debs,
                pip_pkgs=pip_pkgs,
                channel=channel),
            *marks),
        id=id)

def snap(
        snap: str,
        *args: str,
        cmd: Collection[str] = (),
        id=None,
        **kwargs):

    return _dependency(
        cmd=cmd or (snap, *args),
        snap=snap,
        id=id or snap,
        **kwargs
    )

def deb(
        deb: str,
        *args: str,
        cmd: Collection[str] = (),
        debs: Collection[str] = (),
        id: Optional[str] = None,
        **kwargs):

    return _dependency(
        cmd=cmd or (deb, *args),
        debs=debs or (deb,),
        id=id or deb,
        **kwargs)

def pip(
        pkg: str,
        *args: str,
        cmd: Collection[str] = (),
        id: Optional[str] = None,
        **kwargs):
    return _dependency(
        pip_pkgs=(pkg,),
        cmd=cmd or ('python3', '-m', pkg, *args),
        id=id or pkg,
        **kwargs)

def qterminal(*args: str, debs: Collection[str] = ('qterminal', 'qtwayland5'), marks=(), **kwargs):
    marks = (
        pytest.mark.xdg(XDG_CONFIG_HOME={'qterminal.org/qterminal.ini': '[General]\nAskOnExit=false'}),
        *marks)
    return deb('qterminal', *args, debs=debs, marks=marks, **kwargs)

def gedit(*args: str, **kwargs):
    return deb('gedit', '-s', *args, **kwargs)

def wpe(*args: str, cmd: Collection[str] = (), **kwargs):
    return snap('wpe-webkit-mir-kiosk', cmd=cmd or ('wpe-webkit-mir-kiosk.cog', *args), **kwargs)
