from unittest import TestCase
from parameterized import parameterized
import dhall
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


class ParsingTestCase(TestCase):
    def test_single_quote_escaped_string(self):
        # this can be parsed as 4 empty strings or 1 string "''''" - second option is correct
        dhall.parse("''''''''''''''''")
        dhall.parse("'''''''' ''''''''")
