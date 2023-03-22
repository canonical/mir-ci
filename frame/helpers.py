import os
from typing import Iterable

complete_server_list = [
    'ubuntu-frame',
    'mir-kiosk',
    'egmde',
    'confined-shell',
]

def assert_all_are_valid_servers(iterable: Iterable[str]) -> None:
    for i in iterable:
        assert i in complete_server_list, i + ' is not a known server'

def filter_servers(servers: list[str]) -> list[str]:
    assert_all_are_valid_servers(servers)
    allowed_servers = os.environ.get('MIR_TEST_SERVER')
    if allowed_servers:
        allowed_set = set(allowed_servers.split(','))
        assert_all_are_valid_servers(allowed_set)
        return [server for server in servers if server in allowed_set]
    else:
        return servers

def all_servers() -> list[str]:
    return filter_servers(complete_server_list)
