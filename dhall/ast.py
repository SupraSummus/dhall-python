from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class Expression:
    def type(self):
        """Type of this expression"""
        # TODO there will be context passed as a parameter later, propably
        raise NotImplementedError()


@dataclass
class Lambda(Expression):
    parameter_label: str
    parameter_type: Expression
    expression: Expression


@dataclass
class Conditional(Expression):
    condition: Expression
    if_true: Expression
    if_false: Expression


@dataclass
class LetIn(Expression):
    parameters: [(
        str,  # name
        Expression,  # value
        Optional[Expression],  # type
    )]
    expression: Expression


@dataclass
class ForAll(Expression):
    parameter_label: str
    parameter_type: Expression
    expression: Expression


# TODO delete - it's sugar for ForAll
@dataclass
class Arrow(Expression):
    a: Expression
    b: Expression


@dataclass
class TypeBound(Expression):
    expression: Expression
    expression_type: Expression


@dataclass
class BinaryOperatorExpression(Expression):
    arg1: Expression
    arg2: Expression


class ListAppendExpression(BinaryOperatorExpression):
    pass


class ApplicationExpression(BinaryOperatorExpression):
    pass


class MergeExpression(BinaryOperatorExpression):
    pass


class Plus(BinaryOperatorExpression):
    pass


@dataclass
class ImportExpression(Expression):
    source: Any


@dataclass
class SelectExpression(Expression):
    """Select a field from a record"""
    expression: Expression
    label: str

    def type(self):
        if isinstance(self.expression, UnionType):
            self.expression.type()
            return ForAll(
                None,
                self.expression.alternatives_dict[self.label],
                self.expression,
            )

        if isinstance(self.expression, RecordLiteral):
            self.expression.type()
            return self.expression.fields_dict[self.label].type()

        raise TypeError('Can\'t select type from {}'.format(self.expression))


@dataclass
class ProjectionExpression(Expression):
    """Select few field from a record and make a new record out of them"""
    expression: Expression
    labels: [str]

    def type(self):
        expression_type = self.expression.type()
        if not isinstance(expression_type, RecordType):
            raise TypeError('expresion to select fields from must be a record')
        return RecordType([
            (l, expression_type.fields_dict[self.label])
            for l in self.labels
        ])


# literals


@dataclass
class ListLiteral(Expression):
    items: [Expression]


@dataclass
class RecordLiteral(Expression):
    fields: [(str, Expression)]

    def type(self):
        return RecordType([
            (l, val.type())
            for l, val in self.fields
        ])

    @property
    def fields_dict(self):
        return dict(self.fields)


@dataclass
class Union(Expression):
    label: str
    value: Expression
    alternatives: [(str, Expression)]

    def type(self):
        if not unique([self.label] + [a[0] for a in self.alternatives]):
            raise TypeError('nonunique union labels')
        # TODO verify that all expressions are types
        return UnionType([(self.label, self.value.type())] + self.alternatives)


@dataclass
class OptionalLiteral(Expression):
    wrapped: Optional[Expression]


@dataclass
class Identifier(Expression):
    name: str
    scope: Optional[int]


class BuiltinNotImplemented(Expression):
    pass


class NaturalBuiltin(Expression):
    def type(self):
        return TypeBuiltin()


class TextBuiltin(Expression):
    def type(self):
        return TypeBuiltin()


class TypeBuiltin(Expression):
    pass


builtins = {
    'Bool': BuiltinNotImplemented,
    'Optional': BuiltinNotImplemented,
    'None': BuiltinNotImplemented,
    'Natural': NaturalBuiltin,
    'Integer': BuiltinNotImplemented,
    'Double': BuiltinNotImplemented,
    'Text': TextBuiltin,
    'List': BuiltinNotImplemented,
    'True': BuiltinNotImplemented,
    'False': BuiltinNotImplemented,
    'NaN': BuiltinNotImplemented,
    'Infinity': BuiltinNotImplemented,
    'Type': TypeBuiltin,
    'Kind': BuiltinNotImplemented,
    'Sort': BuiltinNotImplemented,
}


def make_builtin_or_identifier(name):
    if name in builtins:
        return builtins[name]()
    return Identifier(name, None)


# types


@dataclass
class ListType(Expression):
    items_type: Expression


@dataclass
class RecordType(Expression):
    fields: [(str, Expression)]

    @property
    def fields_dict(self):
        return dict(self.fields)


@dataclass
class UnionType(Expression):
    alternatives: [(str, Expression)]

    @property
    def alternatives_dict(self):
        return dict(self.alternatives)


@dataclass
class OptionalType(Expression):
    wrapped: Expression
