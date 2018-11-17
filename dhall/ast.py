from typing import Any, Optional
from dataclasses import dataclass

from .data_structures import ShadowDict


def unique(elements):
    return len(elements) == len(set(elements))


def function_check(a, b):
    # TODO
    pass


CTX_EMPTY = ShadowDict()
DEFAULT_VARIABLE_NAME = '_'


@dataclass
class Expression:
    def type(self, ctx=CTX_EMPTY):
        """Type of this expression. ctx contains types for variables."""
        raise NotImplementedError('{}.type() is not implemented yet'.format(self.__class__))

    def normalized(self, ctx=CTX_EMPTY):
        """Perform alpha-normalization. ctx contains new names for variables."""
        raise NotImplementedError('{}.normalized() is not implemented yet'.format(self.__class__))

    def evaluated(self, ctx=CTX_EMPTY):
        """Perform beta-normalization. ctx contains variable values."""
        raise NotImplementedError('{}.evaluated() is not implemented yet'.format(self.__class__))


@dataclass
class Lambda(Expression):
    parameter_label: Optional[str]
    parameter_type: Expression
    expression: Expression

    def normalized(self, ctx=CTX_EMPTY):
        return Lambda(
            None,
            self.parameter_type.normalized(ctx),
            self.expression.normalized(ctx.shadow({
                self.parameter_name: None,
            })),
        )


@dataclass
class Conditional(Expression):
    condition: Expression
    if_true: Expression
    if_false: Expression

    def normalized(self, ctx=CTX_EMPTY):
        return Conditional(
            self.condition.normalized(ctx),
            self.if_true.normalized(ctx),
            self.if_false.normalized(ctx),
        )


@dataclass
class LetIn(Expression):
    parameters: [(
        Optional[str],  # name
        Expression,  # value
        Optional[Expression],  # type
    )]
    expression: Expression

    def normalized(self, ctx=CTX_EMPTY):
        normalized_parameters = [
            (
                None,
                value.normalize(ctx),
                None if typ is None else typ.normalized(ctx),
            )
            for name, value, typ in self.parameters
        ]
        new_ctx = ctx.shadow({
            name: None
            for name, value, typ in self.parameters
        })
        return LetIn(
            normalized_parameters,
            self.expression.normalized(new_ctx),
        )


@dataclass
class ForAll(Expression):
    parameter_label: str
    parameter_type: Expression
    expression: Expression

    def type(self, ctx=CTX_EMPTY):
        parameter_type_type = self.parameter_type.type(ctx)
        expression_type = self.expression.type(ctx.shadow({
            self.parameter_label: self.parameter_type
        }))
        function_check(parameter_type_type, expression_type)
        return expression_type

    def normalized(self, ctx=CTX_EMPTY):
        return ForAll(
            DEFAULT_VARIABLE_NAME,
            self.parameter_type.normalized(ctx),
            self.expression.normalized(ctx.shadow({
                self.parameter_label: DEFAULT_VARIABLE_NAME,
            })),
        )

    def evaluated(self, ctx=CTX_EMPTY):
        return ForAll(
            self.parameter_label,
            self.parameter_type.evaluated(ctx),
            self.expression.evaluated(ctx),
        )


@dataclass
class Variable(Expression):
    name: str
    scope: int = 0

    def normalized(self, ctx=CTX_EMPTY):
        if ctx.has(self.name, self.scope):
            # bound variable
            return Variable(
                ctx.get(self.name, self.scope),
                ctx.age(self.name, self.scope),
            )
        else:
            # free variable
            return self


@dataclass
class TypeAnnotation(Expression):
    expression: Expression
    expression_type: Expression

    def type(self, ctx=CTX_EMPTY):
        self.expression_type.type(ctx)  # the type itself typechecks
        typ = self.expression.type(ctx).evaluated().normalized()
        annotated_type = self.expression_type.evaluated().normalized()
        if annotated_type != typ:
            raise TypeError('annotation {} doesn\'t match expression type {}'.format(annotated_type, typ))
        return self.expression_type


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

    def type(self, ctx=CTX_EMPTY):
        if isinstance(self.expression, UnionType):
            # select from union type yields an union constructor
            self.expression.type(ctx)
            return ForAll(
                DEFAULT_VARIABLE_NAME,
                self.expression.alternatives_dict[self.label],
                self.expression,
            )

        if isinstance(self.expression, RecordLiteral):
            # select from a record yields record field value
            self.expression.type(ctx)
            return self.expression.fields_dict[self.label].type(ctx)

        raise TypeError('Can\'t select from {}'.format(self.expression))


@dataclass
class ProjectionExpression(Expression):
    """Select few field from a record and make a new record out of them"""
    expression: Expression
    labels: [str]

    def type(self, ctx=CTX_EMPTY):
        expression_type = self.expression.type(ctx)
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

    def type(self, ctx=CTX_EMPTY):
        return RecordType([
            (l, val.type(ctx))
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

    def type(self, ctx=CTX_EMPTY):
        if not unique([self.label] + [a[0] for a in self.alternatives]):
            raise TypeError('nonunique union labels')
        # TODO verify that all expressions are types
        return UnionType([(self.label, self.value.type(ctx))] + self.alternatives)


@dataclass
class OptionalLiteral(Expression):
    wrapped: Optional[Expression]

# ### builtins ###


@dataclass(frozen=True)
class BuiltinExpression(Expression):
    def type(self, ctx=CTX_EMPTY):
        return self.builtin_type

    def normalized(self, ctx=CTX_EMPTY):
        return self

    def evaluated(self, ctx=CTX_EMPTY):
        return self


@dataclass(frozen=True)
class SortBuiltin(BuiltinExpression):
    def type(self, ctx=CTX_EMPTY):
        raise TypeError('it\'s impossible to infer type of Sort')


@dataclass(frozen=True)
class KindBuiltin(BuiltinExpression):
    builtin_type = SortBuiltin()


@dataclass(frozen=True)
class TypeBuiltin(BuiltinExpression):
    builtin_type = KindBuiltin()


@dataclass(frozen=True)
class NaturalBuiltin(BuiltinExpression):
    builtin_type = TypeBuiltin()


@dataclass(frozen=True)
class TextBuiltin(BuiltinExpression):
    builtin_type = TypeBuiltin()


@dataclass(frozen=True)
class ListBuiltin(BuiltinExpression):
    builtin_type = ForAll(DEFAULT_VARIABLE_NAME, TypeBuiltin(), TypeBuiltin())


builtins = {
    # 'Bool': BuiltinNotImplemented,
    # 'Optional': BuiltinNotImplemented,
    # 'None': BuiltinNotImplemented,
    'Natural': NaturalBuiltin,
    # 'Integer': BuiltinNotImplemented,
    # 'Double': BuiltinNotImplemented,
    'Text': TextBuiltin,
    'List': ListBuiltin,
    # 'True': BuiltinNotImplemented,
    # 'False': BuiltinNotImplemented,
    # 'NaN': BuiltinNotImplemented,
    # 'Infinity': BuiltinNotImplemented,
    'Type': TypeBuiltin,
    'Kind': KindBuiltin,
    'Sort': SortBuiltin,
}


def make_builtin_or_variable(name):
    if name in builtins:
        return builtins[name]()
    return Variable(name)


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

    def type(self, ctx=CTX_EMPTY):
        if not unique([a[0] for a in self.alternatives]):
            raise TypeError('fields of union type must be unique')
        if len(self.alternatives) == 0:
            return TypeBuiltin()
        typ = self.alternatives[0][1].type(ctx).evaluated()
        if typ not in (TypeBuiltin(), KindBuiltin(), SortBuiltin()):
            raise TypeError('only Types, Kind and Sorts are allowed for union type alternatives')
        for a in self.alternatives[1:]:
            alternative_typ = a[1].type(ctx).evaluated()
            if typ != alternative_typ:
                raise TypeError('all fields on union type must have the same type')
        return typ

    def normalized(self, ctx=CTX_EMPTY):
        return UnionType([
            (name, expr.normalized(ctx))
            for name, expr in self.alternatives
        ])

    def evaluated(self, ctx=CTX_EMPTY):
        return UnionType(sorted([
            (name, expr.evaluated(ctx))
            for name, expr in self.alternatives
        ]))


@dataclass
class OptionalType(Expression):
    wrapped: Expression
