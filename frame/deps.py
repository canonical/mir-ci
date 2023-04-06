import shutil

import types

import pytest

def test_server_dep(server) -> None:
    assert shutil.which(server), f"Server executable not found: {server}"

@pytest.mark.self
def test_mypy_dep(mypy) -> types.ModuleType:
    return __import__('mypy')
