from unittest import TestCase
from parameterized import parameterized
import dhall
import os


def get_tests(dir_path):
    tests = {}
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            name, ext = os.path.splitext(f)
            if ext == '.dhall':
                test_group = tests.setdefault(name[:-1], {})
                assert name[-1] not in test_group
                test_group[name[-1]] = os.path.join(root, f)
    return tests


class TypecheckSuccessSimpleTestCase(TestCase):
    tests = get_tests('./dhall-lang/tests/typecheck/success/simple/')
    # select tests - we dont have full typechecker yet
    tests = {
        '0': tests['0'],
        '1': tests['1'],
        'alternativesAreTypes': tests['alternativesAreTypes'],
    }

    @parameterized.expand(sorted(tests.items()))
    def test(self, _name, paths):
        assert len(paths) == 2  # sanity check
        val = dhall.parser.load(paths['A'])
        typ = dhall.parser.load(paths['B'])
        annotation = dhall.ast.TypeAnnotation(val, typ)
        annotation.type()
