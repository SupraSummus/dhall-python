from typing import Any, Dict, Optional
from dataclasses import dataclass


class Expression:
    pass


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
    parameter_label: str
    parameter_type: Expression
    parameter_value: Expression
    expression: Expression


@dataclass
class ForAll(Expression):
    parameter_label: str
    parameter_type: Expression
    expression: Expression


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


@dataclass
class ImportExpression(Expression):
    source: Any


@dataclass
class SelectorExpression(Expression):
    expression: Expression
    labels: [str]


# literals


@dataclass
class ListLiteral(Expression):
    items: [Expression]


@dataclass
class RecordLiteral(Expression):
    fields: [(str, Expression)]


@dataclass
class OptionalLiteral(Expression):
    wrapped: Optional[Expression]


@dataclass
class Identifier(Expression):
    name: str
    scope: Optional[int]


# types


@dataclass
class ListType(Expression):
    items_type: Expression


@dataclass
class RecordType(Expression):
    fields: Dict[str, Expression]


@dataclass
class OptionalType(Expression):
    wrapped: Expression
