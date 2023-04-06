import shutil

def test_server_dep(server) -> None:
    assert shutil.which(server), f"Server executable not found: {server}"
