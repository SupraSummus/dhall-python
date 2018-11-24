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
            'ignored',
            ast.TypeBuiltin(),
            ast.ListBuiltin().type(),
        )
        self.assertEqual(
            expression.type(),
            typ,
        )
