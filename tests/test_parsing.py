from unittest import TestCase
from parameterized import parameterized
from dhall.parser import parser
import os


class DhallHaskellParsingTestCase(TestCase):
    tests_directory = './dhall-haskell/tests/parser/'
    test_files = [
        f for f in sorted(os.listdir(tests_directory))
        if f.endswith('.dhall') and f not in (
            'pathTermination.dhall',  # this test has missing spaces in application expression
        )
    ]

    @parameterized.expand(test_files)
    def test_parsing(self, filename):
        with open(os.path.join(self.tests_directory, filename), 'rt') as f:
            parser.parse(f.read())
