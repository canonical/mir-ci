import os

import pytest

class TestTest:
    @pytest.mark.self
    def test_project_typechecks(self, mypy) -> None:
        project_path = os.path.dirname(__file__)
        assert os.path.isfile(os.path.join(project_path, 'requirements.txt')), 'project path not detected correctly'
        result = mypy.api.run([project_path])
        if result[2] != 0:
            raise RuntimeError('`$ mypy ' + project_path + '` failed:\n\n' + result[0])
