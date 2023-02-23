from unittest import TestCase
import subprocess
import os

class TestTest(TestCase):
    def test_project_typechecks(self) -> None:
        project_path = os.path.dirname(__file__)
        assert os.path.isfile(os.path.join(project_path, 'requirements.txt')), 'project path not detected correctly'
        result = subprocess.run(
            ['mypy', project_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True)
        if result.returncode != 0:
            raise RuntimeError('`$ mypy ' + project_path + '` failed:\n\n' + result.stdout)
