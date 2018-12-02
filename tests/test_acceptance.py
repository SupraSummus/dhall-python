from unittest import TestCase
from parameterized import parameterized
import dhall
import os


def get_tests(dir_path):
    tests = {}
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            name, ext = os.path.splitext(f)
            assert name not in tests
            tests[name] = os.path.join(root, f)
    return tests


def get_test_sets(dir_path):
    tests = {}
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            name, ext = os.path.splitext(f)
            if ext == '.dhall':
                test_group = tests.setdefault(name[:-1], {})
                assert name[-1] not in test_group
                test_group[name[-1]] = os.path.join(root, f)
    return tests


class ParserSuccessTestCase(TestCase):
    tests = get_test_sets('./dhall-lang/tests/parser/success/')

    @parameterized.expand(sorted(tests.items()))
    def test(self, _name, paths):
        assert len(paths) == 2  # sanity check
        # check if parser accepts the string
        # TODO check against CBOR
        dhall.parser.load(paths['A'])


class ParserFailureTestCase(TestCase):
    tests = get_tests('./dhall-lang/tests/parser/failure/')

    @parameterized.expand(sorted(tests.items()))
    def test(self, _name, path):
        with self.assertRaises(dhall.SyntaxError):
            dhall.parser.load(path)


class TypecheckSuccessSimpleTestCase(TestCase):
    tests = get_test_sets('./dhall-lang/tests/typecheck/success/simple/')
    # select tests - we dont have full typechecker yet
    selected_tests = {
        '0': tests['0'],
        '1': tests['1'],
        'alternativesAreTypes': tests['alternativesAreTypes'],
        'anonymousFunctionsInTypes': tests['anonymousFunctionsInTypes'],
        'fieldsAreTypes': tests['fieldsAreTypes'],
        'kindParameter': tests['kindParameter'],
    }

    @parameterized.expand(sorted(tests.items()))
    def test(self, _name, paths):
        assert len(paths) == 2  # sanity check
        val = dhall.parser.load(paths['A'])
        typ = dhall.parser.load(paths['B'])
        annotation = dhall.ast.TypeAnnotation(val, typ)
        annotation.type()
