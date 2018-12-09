from unittest import TestCase

from dhall import ast


class FunctionTypesTestCase(TestCase):
    def test_function_in_type(self):
        expression = ast.LetIn(
            [(
                'f',
                ast.Lambda('a', ast.KindBuiltin(), ast.Variable('a')),
                None,
            )],
            ast.Lambda(
                'ignored',
                ast.ApplicationExpression(ast.Variable('f'), ast.TypeBuiltin()),
                ast.ListBuiltin(),
            ),
        )
        typ = ast.ForAll(
            '_',
            ast.TypeBuiltin(),
            ast.ListBuiltin().type()[0],
        )
        self.assertEqual(
            expression.normalized_type(),
            typ,
        )
