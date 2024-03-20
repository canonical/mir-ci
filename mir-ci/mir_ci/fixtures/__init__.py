from typing import Any, Collection, Optional, Union

import pytest

from ..program.app import App, AppType


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
