import os
import subprocess

import pytest

class TestTest:
    @pytest.mark.self
    @pytest.mark.deps('python3', '-m', 'mypy', pip_pkgs=('mypy',))
    def test_project_typechecks(self, deps) -> None:
        project_path = os.path.dirname(__file__)
        assert os.path.isfile(os.path.join(project_path, 'requirements.txt')), 'project path not detected correctly'
        result = subprocess.run(
            [*deps, project_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True)
        if result.returncode != 0:
            raise RuntimeError('`$ mypy ' + project_path + '` failed:\n\n' + result.stdout)
