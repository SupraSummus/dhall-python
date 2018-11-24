from unittest import TestCase
import dhall


class ParsingTestCase(TestCase):
    def test_single_quote_escaped_string(self):
        # this can be parsed as 4 empty strings or 1 string "''''" - second option is correct
        dhall.parse("''''''''''''''''")
        dhall.parse("'''''''' ''''''''")
