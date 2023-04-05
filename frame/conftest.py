import shutil

import pytest

@pytest.fixture(scope="session", params=(
  'ubuntu-frame',
  'mir-kiosk',
  'egmde',
  'confined-shell',
  'mir_demo_server',
))
def server(request):
    if shutil.which(request.param) is None:
        pytest.skip(f'server executable not found: {request.param}')
    else:
        return request.param
