from . import deb, snap


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
