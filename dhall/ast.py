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
class LetIn(Lambda):
    parameter_label: str
    parameter_value: Expression
    parameter_type: Expression
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
class ListAppendExpression(Expression):
    expressions: [Expression]
