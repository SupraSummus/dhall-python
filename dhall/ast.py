from typing import Any, Optional
from dataclasses import dataclass

from .data_structures import ShadowDict


def unique(elements):
    return len(elements) == len(set(elements))


def function_check(arg, result):
    if result == TypeBuiltin():
        return TypeBuiltin()
    if arg == KindBuiltin() and result == KindBuiltin():
        return KindBuiltin()
    if arg == SortBuiltin() and result in (KindBuiltin(), SortBuiltin()):
        return SortBuiltin()
    raise TypeError('Function check failed for `{} ↝ {}`'.format(
        arg.to_dhall(),
        result.to_dhall(),
    ))


CTX_EMPTY = ShadowDict()
DEFAULT_VARIABLE_NAME = '_'


@dataclass
class Expression:
    def normalized(self, ctx=CTX_EMPTY):
        """Perform alpha-normalization. ctx contains new names for variables."""
        return self._normalized(ctx)

    def _normalized(self, ctx):
        raise NotImplementedError('{}._normalized() is not implemented yet'.format(self.__class__))

    def evaluated(self, ctx=CTX_EMPTY):
        """Perform beta-normalization. ctx contains variable values."""
        return self._evaluated(ctx)

    def _evaluated(self, ctx):
        raise NotImplementedError('{}._evaluated() is not implemented yet'.format(self.__class__))

    def type(self, type_ctx=CTX_EMPTY, value_ctx=CTX_EMPTY):
        """Type of this expression. ctx contains types for variables."""
        return self._type(type_ctx, value_ctx)

    def _type(self, type_ctx, value_ctx):
        raise NotImplementedError('{}._type() is not implemented yet'.format(self.__class__))

    def exact(self, other):
        """self ≡ other"""
        return isinstance(other, Expression) and self.evaluated().normalized() == other.evaluated().normalized()

    def to_dhall(self):
        return str(self)  # TODO change to not implemented someday

    def to_python(self):
        """Representation in python's native data types."""
        raise NotImplementedError('{}.to_python() is not implemented yet'.format(self.__class__))


@dataclass
class Lambda(Expression):
    parameter_name: str
    parameter_type: Expression
    expression: Expression

    def normalized(self, ctx=CTX_EMPTY):
        return Lambda(
            DEFAULT_VARIABLE_NAME,
            self.parameter_type.normalized(ctx),
            self.expression.normalized(ctx.shadow({
                self.parameter_name: DEFAULT_VARIABLE_NAME,
            })),
        )

    def evaluated(self, ctx=CTX_EMPTY):
        return Lambda(
            self.parameter_name,
            self.parameter_type.evaluated(ctx),
            self.expression.evaluated(ctx),
        )

    def _type(self, type_ctx, value_ctx):
        expression_type = self.expression.type(type_ctx.shadow({
            self.parameter_name: self.parameter_type,
        }), value_ctx).evaluated(value_ctx)
        lambda_type = ForAll(
            self.parameter_name,
            self.parameter_type.evaluated(value_ctx),
            expression_type,
        )
        lambda_type.type(type_ctx, value_ctx)
        return lambda_type

    def to_dhall(self):
        return 'λ({} : {}) → {}'.format(
            self.parameter_name,
            self.parameter_type.to_dhall(),
            self.expression.to_dhall(),
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
        str,  # name
        Expression,  # value
        Optional[Expression],  # type
    )]
    expression: Expression

    def normalized(self, ctx=CTX_EMPTY):
        normalized_parameters = [
            (
                DEFAULT_VARIABLE_NAME,
                value.normalize(ctx),
                None if typ is None else typ.normalized(ctx),
            )
            for name, value, typ in self.parameters
        ]
        new_ctx = ctx.shadow({
            name: DEFAULT_VARIABLE_NAME
            for name, value, typ in self.parameters
        })
        return LetIn(
            normalized_parameters,
            self.expression.normalized(new_ctx),
        )

    def evaluated(self, ctx=CTX_EMPTY):
        return self.expression.evaluated(ctx.shadow({
            name: value.evaluated(ctx)
            for name, value, typ in self.parameters
        }))

    def _type(self, type_ctx, value_ctx):
        for name, value, typ in self.parameters:
            value_type = value.type(type_ctx, value_ctx)

            # verify against annotation
            if typ is not None:
                typ.type(type_ctx, value_ctx)
                if not typ.exact(value_type):
                    raise TypeError('annotation\n\t{} doesn\'t match expression type\n\t{}'.format(
                        typ.to_dhall(),
                        value_type.to_dhall(),
                    ))

            value_ctx = value_ctx.shadow({
                name: value.evaluated(value_ctx),
            })

        return self.expression.type(type_ctx, value_ctx)


@dataclass
class ForAll(Expression):
    parameter_name: str
    parameter_type: Expression
    expression: Expression

    def normalized(self, ctx=CTX_EMPTY):
        return ForAll(
            DEFAULT_VARIABLE_NAME,
            self.parameter_type.normalized(ctx),
            self.expression.normalized(ctx.shadow({
                self.parameter_name: DEFAULT_VARIABLE_NAME,
            })),
        )

    def evaluated(self, ctx=CTX_EMPTY):
        return ForAll(
            self.parameter_name,
            self.parameter_type.evaluated(ctx),
            self.expression.evaluated(ctx),
        )

    def _type(self, type_ctx, value_ctx):
        parameter_type_type = self.parameter_type.type(type_ctx, value_ctx).evaluated().normalized()
        expression_type = self.expression.type(type_ctx.shadow({
            self.parameter_name: self.parameter_type
        }), value_ctx).evaluated().normalized()
        return function_check(parameter_type_type, expression_type)

    def to_dhall(self):
        return '∀({} : {}) → {}'.format(
            self.parameter_name,
            self.parameter_type.to_dhall(),
            self.expression.to_dhall(),
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

    def evaluated(self, ctx=CTX_EMPTY):
        if ctx.has(self.name, self.scope):
            return ctx.get(self.name, self.scope)
        else:
            return self
            raise TypeError('unbound variable {}'.format(self))

    def _type(self, type_ctx, value_ctx):
        if value_ctx.has(self.name, self.scope):
            return value_ctx.get(self.name, self.scope).type(type_ctx, value_ctx)
        elif type_ctx.has(self.name, self.scope):
            return type_ctx.get(self.name, self.scope)
        else:
            raise TypeError('unbound variable {}'.format(self))

    def __str__(self):
        return '{}@{}'.format(self.name, self.scope)


@dataclass
class TypeAnnotation(Expression):
    expression: Expression
    expression_type: Expression

    def _type(self, type_ctx, value_ctx):
        self.expression_type.type(type_ctx, value_ctx)  # the type itself typechecks
        typ = self.expression.type(type_ctx, value_ctx)
        if not self.expression_type.exact(typ):
            raise TypeError('annotation\n\t`{}` doesn\'t match expression type\n\t`{}`'.format(
                self.expression_type.to_dhall(),
                typ.to_dhall(),
            ))
        return self.expression_type


@dataclass(frozen=True)
class BinaryOperatorExpression(Expression):
    arg1: Expression
    arg2: Expression

    def normalized(self, ctx=CTX_EMPTY):
        return self.__class__(
            self.arg1.normalized(ctx),
            self.arg2.normalized(ctx),
        )


class ListAppendExpression(BinaryOperatorExpression):
    pass


@dataclass(frozen=True)
class ApplicationExpression(BinaryOperatorExpression):
    def evaluated(self, ctx=CTX_EMPTY):
        f = self.arg1.evaluated(ctx)
        arg = self.arg2.evaluated(ctx)
        if isinstance(f, Lambda):
            return f.expression.evaluated(ctx.shadow({
                f.parameter_name: arg,
            }))
        else:
            return ApplicationExpression(f, arg)

    def _type(self, type_ctx, value_ctx):
        function_type = self.arg1.type(type_ctx, value_ctx).evaluated().normalized()
        if not isinstance(function_type, ForAll):
            raise TypeError('couldnt apply non-function `{}`'.format(function_type.to_dhall()))
        parameter_type = self.arg2.type(type_ctx, value_ctx)
        if not parameter_type.exact(function_type.parameter_type):
            raise TypeError('Function expects argument of type {}, but got {}.'.format(
                function_type.parameter_type,
                parameter_type,
            ))
        return function_type.expression.evaluated(value_ctx)

    def to_dhall(self):
        return '({} {})'.format(self.arg1.to_dhall(), self.arg2.to_dhall())


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

    def _type(self, type_ctx, value_ctx):
        if isinstance(self.expression, UnionType):
            # select from union type yields an union constructor
            self.expression.type(type_ctx, value_ctx)
            return ForAll(
                DEFAULT_VARIABLE_NAME,
                self.expression.alternatives_dict[self.label],
                self.expression,
            )

        if isinstance(self.expression, RecordLiteral):
            # select from a record yields record field value
            self.expression.type(type_ctx, value_ctx)
            return self.expression.fields_dict[self.label].type(type_ctx, value_ctx)

        raise TypeError('Can\'t select from {}'.format(self.expression))


@dataclass
class ProjectionExpression(Expression):
    """Select few field from a record and make a new record out of them"""
    expression: Expression
    labels: [str]

    def _type(self, type_ctx, value_ctx):
        expression_type = self.expression.type(type_ctx, value_ctx)
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

    def _type(self, type_ctx, value_ctx):
        return RecordType([
            (l, val.type(type_ctx, value_ctx))
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

    def _type(self, type_ctx, value_ctx):
        if not unique([self.label] + [a[0] for a in self.alternatives]):
            raise TypeError('nonunique union labels')
        # TODO verify that all expressions are types
        return UnionType([(self.label, self.value.type(type_ctx, value_ctx))] + self.alternatives)


@dataclass
class OptionalLiteral(Expression):
    wrapped: Optional[Expression]

# ### builtins ###


@dataclass(frozen=True)
class BuiltinExpression(Expression):
    def _type(self, type_ctx, value_ctx):
        return self.builtin_type

    def normalized(self, ctx=CTX_EMPTY):
        return self

    def evaluated(self, ctx=CTX_EMPTY):
        return self

    def to_dhall(self):
        return self.dhall_string


@dataclass(frozen=True)
class SortBuiltin(BuiltinExpression):
    dhall_string = 'Sort'

    def _type(self, type_ctx, value_ctx):
        raise TypeError('it\'s impossible to infer type of Sort')


@dataclass(frozen=True)
class KindBuiltin(BuiltinExpression):
    builtin_type = SortBuiltin()
    dhall_string = 'Kind'


@dataclass(frozen=True)
class TypeBuiltin(BuiltinExpression):
    builtin_type = KindBuiltin()
    dhall_string = 'Type'


@dataclass(frozen=True)
class NaturalBuiltin(BuiltinExpression):
    builtin_type = TypeBuiltin()
    dhall_string = 'Natural'


@dataclass(frozen=True)
class TextBuiltin(BuiltinExpression):
    builtin_type = TypeBuiltin()
    dhall_string = 'Text'


@dataclass(frozen=True)
class ListBuiltin(BuiltinExpression):
    builtin_type = ForAll(DEFAULT_VARIABLE_NAME, TypeBuiltin(), TypeBuiltin())
    dhall_string = 'List'


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

    def _type(self, type_ctx, value_ctx):
        if not unique([a[0] for a in self.alternatives]):
            raise TypeError('fields of union type must be unique')
        if len(self.alternatives) == 0:
            return TypeBuiltin()
        typ = self.alternatives[0][1].type(type_ctx, value_ctx).evaluated()
        if typ not in (TypeBuiltin(), KindBuiltin(), SortBuiltin()):
            raise TypeError('only Types, Kind and Sorts are allowed for union type alternatives')
        for a in self.alternatives[1:]:
            alternative_typ = a[1].type(type_ctx, value_ctx).evaluated()
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
