from unittest import TestCase

from dhall.data_structures import ShadowDict


class ShadowDictTestCase(TestCase):
    def test_get_top(self):
        self.assertEqual(
            ShadowDict().shadow({'k': 'v'}).get('k'),
            'v',
        )

    def test_get_top_shadowed(self):
        self.assertEqual(
            ShadowDict().shadow({'k': 'v'}).shadow({'k': 'vv'}).get('k'),
            'vv',
        )

    def test_get_top_other_shadowed(self):
        self.assertEqual(
            ShadowDict().shadow({'k': 'v'}).shadow({'k2': 'v2'}).get('k'),
            'v',
        )

    def test_get_deep_shadowed(self):
        self.assertEqual(
            ShadowDict().shadow({'k': 'v'}).shadow({'k': 'v2'}).get('k', 1),
            'v',
        )

    def test_has_shadowed(self):
        self.assertFalse(
            ShadowDict().shadow({'k': 'v'}).shadow({'k': 'v2'}).has('k', 2),
        )

    def test_age(self):
        self.assertEqual(
            ShadowDict().shadow({'k': 'v'}).shadow({}).shadow({'k': 'v2'}).age('k', 1),
            2,
        )
