from typing import Any, Optional
from dataclasses import dataclass

from .data_structures import ShadowDict


CTX_EMPTY = ShadowDict()
DEFAULT_VARIABLE_NAME = '_'


def unique(elements):
    return len(elements) == len(set(elements))


def exact(a, b, ctx=CTX_EMPTY):
    """a ≡ b"""
    return a.evaluated(ctx).normalized() == b.evaluated(ctx).normalized()


def function_check(arg, result):
    """arg ↝ result : return"""
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


def increase_indent(s):
    return '\t' + s.replace('\n', '\n\t')


def ctx_empty(ctx):
    for k, vs in ctx.entries.items():
        for (typ, value, covered_ctx), _ in vs:
            if typ is not None or value is not None:
                return False
    return True


def ctx2str(ctx):
    parts = []
    for k, vs in sorted(ctx.entries.items()):
        for scope, ((typ, value, covered_ctx), _) in enumerate(vs):

            if typ is not None:
                s = '`{}@{}` has type `{}`'.format(
                    k, scope, typ.to_dhall(),
                )
            if value is not None:
                s = '`{}@{}` has value `{}`'.format(
                    k, scope, value.to_dhall(),
                )

            covered_ctx_str = ctx2str(covered_ctx)
            if covered_ctx_str:
                s += ' where \n' + increase_indent(covered_ctx_str)

            parts.append(s)

    return '\n'.join(parts)


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

    def type(self, type_ctx=CTX_EMPTY):
        """Type of this expression.
        type_ctx contains types for variables.
        value_ctx contains variable values to substitute
        """
        try:
            return self._type(type_ctx)
        except TypeError:
            raise TypeError("when type-infering\n"
                            "\t`{}`\n{}".format(
                self.to_dhall(),
                ctx2str(type_ctx),
            ))

    def _type(self, type_ctx):
        raise NotImplementedError('{}._type() is not implemented yet'.format(self.__class__))

    def normalized_type(self, type_ctx=CTX_EMPTY):
        """self :⇥ return"""
        typ, typ_ctx = self.type(type_ctx)
        return typ.evaluated(typ_ctx).normalized()

    def exact(self, other, ctx=CTX_EMPTY):
        """self ≡ other"""
        return exact(self, other, ctx)

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

    def _normalized(self, ctx):
        return Lambda(
            DEFAULT_VARIABLE_NAME,
            self.parameter_type.normalized(ctx),
            self.expression.normalized(ctx.shadow({
                self.parameter_name: DEFAULT_VARIABLE_NAME,
            })),
        )

    def _evaluated(self, ctx):
        return Lambda(
            self.parameter_name,
            self.parameter_type.evaluated(ctx),
            self.expression.evaluated(ctx.shadow({
                self.parameter_name: (None, None, None),
            })),
        )

    def _type(self, type_ctx):
        expression_type = self.expression.type(type_ctx.shadow({
            self.parameter_name: (self.parameter_type, None, type_ctx),
        }))
        lambda_type = ForAll(
            self.parameter_name,
            self.parameter_type,
            expression_type,
        )
        lambda_type.type(type_ctx)  # lambda type must typecheck
        return lambda_type, type_ctx

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

    def _normalized(self, ctx):
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

    def _normalized(self, ctx):
        normalized_parameters = []
        for name, value, typ in self.parameters:
            normalized_parameters.append((
                DEFAULT_VARIABLE_NAME,
                value.normalized(ctx),
                None if typ is None else typ.normalized(ctx),
            ))
            ctx = ctx.shadow({
                name: DEFAULT_VARIABLE_NAME,
            })
        return LetIn(
            normalized_parameters,
            self.expression.normalized(ctx),
        )

    def _evaluated(self, ctx):
        for name, value, typ in self.parameters:
            ctx = ctx.shadow({
                name: (None, value, ctx),
            })
        return self.expression.evaluated(ctx)

    def _type(self, type_ctx):
        for name, value, typ in self.parameters:
            value_type, value_type_ctx = value.type(type_ctx)

            # verify against annotation
            if typ is not None:
                typ.type(type_ctx)  # type annotation typechecks itself
                if not exact(typ, value_type):
                    raise TypeError('annotation\n\t{} doesn\'t match expression type\n\t{}'.format(
                        typ.to_dhall(),
                        value_type.to_dhall(),
                    ))

            type_ctx = type_ctx.shadow({
                name: (None, value, type_ctx),
            })

        return self.expression.type(type_ctx)

    def to_dhall(self):
        lets = []
        for name, value, typ in self.parameters:
            if typ is None:
                lets.append('let {} = {}'.format(name, value.to_dhall()))
            else:
                lets.append('let {} = {} : {}'.format(name, value.to_dhall(), typ.to_dhall()))
        return '{} in {}'.format(' '.join(lets), self.expression.to_dhall())


@dataclass
class ForAll(Expression):
    parameter_name: str
    parameter_type: Expression
    expression: Expression

    def _normalized(self, ctx):
        return ForAll(
            DEFAULT_VARIABLE_NAME,
            self.parameter_type.normalized(ctx),
            self.expression.normalized(ctx.shadow({
                self.parameter_name: DEFAULT_VARIABLE_NAME,
            })),
        )

    def _evaluated(self, ctx):
        return ForAll(
            self.parameter_name,
            self.parameter_type.evaluated(ctx),
            self.expression.evaluated(ctx.shadow({
                self.parameter_name: (None, None, ctx),
            })),
        )

    def _type(self, type_ctx):
        parameter_type_type = self.parameter_type.normalized_type(type_ctx)
        expression_type = self.expression.normalized_type(type_ctx.shadow({
            self.parameter_name: (self.parameter_type, None, type_ctx),
        }))
        return function_check(parameter_type_type, expression_type), CTX_EMPTY

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

    def _normalized(self, ctx):
        if ctx.has(self.name, self.scope):
            # bound variable
            return Variable(
                ctx.get(self.name, self.scope),
                ctx.age(self.name, self.scope),
            )
        else:
            # free variable
            return self

    def _evaluated(self, ctx):
        if ctx.has(self.name, self.scope):
            _, value, covered_ctx = ctx.get(self.name, self.scope)
            if value is not None:
                return value.evaluated(covered_ctx)

        return self

    def _type(self, type_ctx):
        if type_ctx.has(self.name, self.scope):
            typ, value, covered_ctx = type_ctx.get(self.name, self.scope)
            if value is not None:
                return value.type(covered_ctx), covered_ctx
            if typ is not None:
                return typ, covered_ctx

        raise TypeError('unbound variable {}'.format(self))

    def __str__(self):
        return '{}@{}'.format(self.name, self.scope)


@dataclass
class TypeAnnotation(Expression):
    expression: Expression
    expression_type: Expression

    def _type(self, type_ctx):
        self.expression_type.type(type_ctx)  # the type itself typechecks
        typ, typ_ctx = self.expression.type(type_ctx)
        annotated_type = self.expression_type
        if typ.evaluated(typ_ctx).normalized() != annotated_type.evaluated(type_ctx).normalized():
            raise TypeError('annotation\n\t`{}` doesn\'t match expression type\n\t`{}`'.format(
                self.expression_type.to_dhall(),
                typ.to_dhall(),
            ))
        return annotated_type, type_ctx


@dataclass(frozen=True)
class BinaryOperatorExpression(Expression):
    arg1: Expression
    arg2: Expression

    def _normalized(self, ctx):
        return self.__class__(
            self.arg1.normalized(ctx),
            self.arg2.normalized(ctx),
        )


class ListAppendExpression(BinaryOperatorExpression):
    pass


@dataclass(frozen=True)
class ApplicationExpression(BinaryOperatorExpression):
    def _evaluated(self, ctx):
        f = self.arg1.evaluated(ctx)
        arg = self.arg2.evaluated(ctx)
        if isinstance(f, Lambda):
            return f.expression.evaluated(ctx.shadow({
                f.parameter_name: (None, arg, ctx),
            }))
        else:
            return ApplicationExpression(f, arg)

    def _type(self, type_ctx):
        function_type = self.arg1.normalized_type(type_ctx)
        if not isinstance(function_type, ForAll):
            raise TypeError('couldnt apply non-function `{}`'.format(self.arg1.to_dhall()))
        parameter_type, parameter_type_ctx = self.arg2.type(type_ctx)
        if not exact(parameter_type, function_type.parameter_type):
            raise TypeError('Function expects argument of type {}, but got {}.'.format(
                function_type.parameter_type,
                parameter_type,
            ))
        return function_type.expression, type_ctx.shadow({
            function_type.parameter_name: (None, self.arg2, parameter_type_ctx),
        })

    def to_dhall(self):
        return '({} {})'.format(self.arg1.to_dhall(), self.arg2.to_dhall())


@dataclass(frozen=True)
class MergeExpression(Expression):
    handlers: Expression
    union: Expression
    result_type: Optional[Expression] = None

    def _type(self, type_ctx):
        handlers_type = self.handlers.normalized_type(type_ctx)
        if not isinstance(handlers_type, RecordType):
            raise TypeError("expected record as a first argument to `merge` but `{}` has type `{}`".format(
                self.handlers.to_dhall(), handlers_type.to_dhall(),
            ))

        union_type = self.union.normalized_type(type_ctx)
        if not isinstance(union_type, UnionType):
            raise TypeError("expected union as a second argument to `merge` but `{}` has type `{}`".format(
                self.union.to_dhall(), union_type.to_dhall(),
            ))

        handlers_type_fields = sorted(handlers_type.fields)
        union_type_alternatives = sorted(union_type.alternatives)

        if [f[0] for f in handlers_type_fields] != [f[0] for f in union_type_alternatives]:
            raise TypeError("union and handlers must have exactly same field names set")

        output_type = None
        output_type_ctx = None
        if self.result_type is not None:
            output_type = self.result_type.evaluated(type_ctx)
            output_type_ctx = type_ctx
        for (name, handler_type), (_, input_type) in zip(handlers_type_fields, union_type_alternatives):
            if not isinstance(handler_type, ForAll):
                raise TypeError("handler for field `{}` is not a function, but {}".format(
                    name,
                    handler_type.to_dhall(),
                ))
            if not exact(handler_type.parameter_type, input_type):
                raise TypeError("handler for field `{}` expects `{}` as input, but union contains `{}`".format(
                    name,
                    handler_type.parameter_type.format(),
                    input_type.format(),
                ))
            new_output_type = handler_type.expression
            new_output_type_ctx = type_ctx.shadow({
                handler_type.parameter_name: (None, None, None),  # require that this is not a free variable
            })
            if output_type is not None:
                if output_type.evaluated(output_type_ctx).normalized() != new_output_type.evaluated(new_output_type_ctx).normalized():
                    raise TypeError('not matching handlers output types: `{}` and `{}`'.format(
                        output_type.to_dhall(),
                        new_output_type.to_dhall(),
                    ))
            output_type = new_output_type
            output_type_ctx = new_output_type_ctx

        if output_type is None:
            raise TypeError('empty merge expression without type annotation')
        else:
            return output_type, output_type_ctx


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

    def _type(self, type_ctx):
        if isinstance(self.expression, UnionType):
            # select from union type yields an union constructor
            self.expression.type(type_ctx)
            return ForAll(
                DEFAULT_VARIABLE_NAME,
                self.expression.alternatives_dict[self.label],
                self.expression,
            ), type_ctx.shadow({
                DEFAULT_VARIABLE_NAME, (None, None, None),
            })

        if isinstance(self.expression, RecordLiteral):
            # select from a record yields record field value
            self.expression.type(type_ctx)
            return self.expression.fields_dict[self.label].type(type_ctx), type_ctx

        raise TypeError('Can\'t select from {}'.format(self.expression))


@dataclass
class ProjectionExpression(Expression):
    """Select few field from a record and make a new record out of them"""
    expression: Expression
    labels: [str]

    def _type(self, type_ctx):
        expression_type = self.expression.type(type_ctx)
        if not isinstance(expression_type, RecordType):
            raise TypeError('expresion to select fields from must be a record')
        return RecordType([
            (l, expression_type.fields_dict[self.label])
            for l in self.labels
        ]), type_ctx


# literals


@dataclass
class ListLiteral(Expression):
    items: [Expression]


@dataclass
class RecordLiteral(Expression):
    fields: [(str, Expression)]

    def _type(self, type_ctx):
        return RecordType([
            (l, val.type(type_ctx))
            for l, val in self.fields
        ]), type_ctx

    @property
    def fields_dict(self):
        return dict(self.fields)


@dataclass
class Union(Expression):
    label: str
    value: Expression
    alternatives: [(str, Expression)]

    def _type(self, type_ctx):
        if not unique([self.label] + [a[0] for a in self.alternatives]):
            raise TypeError('nonunique union labels')
        # TODO verify that all expressions are types
        return UnionType([(self.label, self.value.type(type_ctx))] + self.alternatives), type_ctx


@dataclass
class OptionalLiteral(Expression):
    wrapped: Optional[Expression] = None

# ### builtins ###


@dataclass(frozen=True)
class BuiltinExpression(Expression):
    def _type(self, type_ctx):
        return self.builtin_type, CTX_EMPTY

    def _normalized(self, ctx):
        return self

    def _evaluated(self, ctx):
        return self

    def to_dhall(self):
        return self.dhall_string


@dataclass(frozen=True)
class SortBuiltin(BuiltinExpression):
    dhall_string = 'Sort'

    def _type(self, type_ctx):
        raise TypeError('it\'s impossible to infer type of `Sort`')


@dataclass(frozen=True)
class KindBuiltin(BuiltinExpression):
    builtin_type = SortBuiltin()
    dhall_string = 'Kind'


@dataclass(frozen=True)
class TypeBuiltin(BuiltinExpression):
    builtin_type = KindBuiltin()
    dhall_string = 'Type'


@dataclass(frozen=True)
class BoolBuiltin(BuiltinExpression):
    builtin_type = TypeBuiltin()
    dhall_string = 'Bool'


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


_builtins = {
    builtin.dhall_string: builtin
    for builtin in [
        BoolBuiltin,
        # 'Optional': BuiltinNotImplemented,
        # 'None': BuiltinNotImplemented,
        NaturalBuiltin,
        # 'Integer': BuiltinNotImplemented,
        # 'Double': BuiltinNotImplemented,
        TextBuiltin,
        ListBuiltin,
        # 'True': BuiltinNotImplemented,
        # 'False': BuiltinNotImplemented,
        # 'NaN': BuiltinNotImplemented,
        # 'Infinity': BuiltinNotImplemented,
        TypeBuiltin,
        KindBuiltin,
        SortBuiltin,
    ]
}


def make_builtin_or_variable(name):
    if name in _builtins:
        return _builtins[name]()
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

    def _normalized(self, ctx):
        return RecordType([
            (name, expression.normalized(ctx))
            for name, expression in self.fields
        ])

    def _evaluated(self, ctx):
        return RecordType([
            (name, expression.evaluated(ctx))
            for name, expression in self.fields
        ])

    def _type(self, type_ctx):
        if not self.fields:
            return TypeBuiltin()
        field_types = []
        for name, expression in self.fields:
            typ = expression.normalized_type(type_ctx)
            if typ == SortBuiltin() and not exact(expression, KindBuiltin()):
                raise TypeError("expected `Kind` in a record type field, but got {}".format(
                    expression.to_dhall(),
                ))
            field_types.append(typ)
        if all(t == TypeBuiltin() for t in field_types):
            return TypeBuiltin(), CTX_EMPTY
        if all(t in (KindBuiltin(), TypeBuiltin()) for t in field_types):
            return SortBuiltin(), CTX_EMPTY
        raise TypeError("all record type members must be of type Type, or all must be of type Kind or Sort")


@dataclass
class UnionType(Expression):
    alternatives: [(str, Expression)]

    @property
    def alternatives_dict(self):
        return dict(self.alternatives)

    def _type(self, type_ctx):
        if not unique([a[0] for a in self.alternatives]):
            raise TypeError('fields of union type must be unique')
        if len(self.alternatives) == 0:
            return TypeBuiltin(), CTX_EMPTY
        typ = self.alternatives[0][1].normalized_type(type_ctx)
        if typ not in (TypeBuiltin(), KindBuiltin(), SortBuiltin()):
            raise TypeError('only Types, Kind and Sorts are allowed for union type alternatives')
        for a in self.alternatives[1:]:
            alternative_typ = a[1].normalized_type(type_ctx)
            if typ != alternative_typ:
                raise TypeError('all fields on union type must have the same type')
        return typ, CTX_EMPTY

    def _normalized(self, ctx):
        return UnionType([
            (name, expr.normalized(ctx))
            for name, expr in self.alternatives
        ])

    def _evaluated(self, ctx):
        return UnionType(sorted([
            (name, expr.evaluated(ctx))
            for name, expr in self.alternatives
        ]))


@dataclass
class OptionalType(Expression):
    wrapped: Expression
