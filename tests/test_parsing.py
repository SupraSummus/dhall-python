from unittest import TestCase
from parameterized import parameterized
from dhall.parser import parser
import os


class DhallHaskellParsingTestCase(TestCase):
    tests_directory = './dhall-haskell/tests/parser/'

    @parameterized.expand(sorted(os.listdir(tests_directory)))
    def test_parsing(self, filename):
        with open(os.path.join(self.tests_directory, filename), 'rt') as f:
            parser.parse(f.read())
