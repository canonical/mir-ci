import pytest

from typing import Optional, Union, Collection

def snap(
        snap: str,
        *args: str,
        channel: str = 'latest/stable',
        cmd: Collection[str] = (),
        marks: Union[pytest.MarkDecorator, Collection[Union[pytest.MarkDecorator, pytest.Mark]]] = (),
        id: Optional[str] = None):

    if isinstance(marks, pytest.Mark):
        marks = (marks,)

    return pytest.param(
        cmd or (snap, *args),
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
        id: Optional[str] = None):
    if isinstance(marks, pytest.Mark):
        marks = (marks,)

    return pytest.param(
        cmd or (deb, *args),
        marks=(                             # type: ignore
            pytest.mark.deps(
                cmd=cmd or (deb, *args),
                debs=debs or (deb,)),
            *marks),
        id=id or deb)

def qterminal(*args: str, debs: Collection[str] = ('qterminal', 'qtwayland5'), **kwargs):
    return deb('qterminal', *args, debs=debs, **kwargs)

def gedit(*args: str, **kwargs):
    return deb('gedit', '-s', *args, **kwargs)

def wpe(*args: str, cmd: Collection[str] = (), **kwargs):
    return snap('wpe-webkit-mir-kiosk', cmd=cmd or ('wpe-webkit-mir-kiosk.cog', *args), **kwargs)
