from unittest import TestCase
from parameterized import parameterized
from dhall import parser
import os


class DhallHaskellParsingTestCase(TestCase):
    tests_directory = './dhall-haskell/dhall/tests/parser/'
    test_files = [
        f for f in sorted(os.listdir(tests_directory))
        if f.endswith('.dhall') and f not in (
            'pathTermination.dhall',  # this test has missing spaces in application expression
        )
    ]

    @parameterized.expand(test_files)
    def test(self, filename):
        parser.load(os.path.join(self.tests_directory, filename))
