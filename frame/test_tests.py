from unittest import TestCase
import subprocess
import os

from helpers import combine

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

    def test_combine(self) -> None:
        self.assertEqual(
            combine([1, 2, 3], ['a', 'b']),
            [
                (1, 'a'),
                (1, 'b'),
                (2, 'a'),
                (2, 'b'),
                (3, 'a'),
                (3, 'b'),
            ])
