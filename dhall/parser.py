from tools import timeit
import parglare

from . import ast
from .parglare_adapter import to_parglare_grammar


with timeit('importing grammar'):
    from ._grammar import grammar
    productions, terminals, original_start_symbol, start_symbol, parse_table = grammar


def concat_all(*args):
    c = []
    for a in args:
        if isinstance(a, (list, tuple)):
            c.append(concat_all(*a))
        else:
            c.append(a)
    return ''.join(c)


def identity(a):
    return a


def identity_list(*a):
    return a


def collect_many(c, indexes):
    items = []
    while len(c) != 0:
        items.append(tuple(c[i + 1] for i in indexes))
        c = c[0]
    items.reverse()
    return items


def collect(c, i):
    return [e[0] for e in collect_many(c, (i,))]


def _operator_wrapper(f):
    def g(*c):
        return f(c[0], c[-1])
    return g


actions = {}

actions[start_symbol] = [lambda a, _: a]
actions[original_start_symbol] = [lambda _, a: a]

actions['simple-label'] = [concat_all]
actions['quoted-label'] = [concat_all]
actions['label'] = [lambda c, _ws: c if isinstance(c, str) else c[1]]

actions['natural-raw'] = [lambda f, c: int(f + ''.join(collect(c, 0)))]
actions['natural-literal'] = [lambda a, _: a]

actions['expression'] = [
    # lambda
    lambda _1, _2, label, _3, typ, _4, _5, expr: ast.Lambda(label, typ, expr),
    # conditional
    lambda _1, condition, _2, if_true, _3, if_false: ast.Conditional(condition, if_true, if_false),
    # let .. = .. in ..
    lambda _let, label, maybe_type, _eq, value, more_lets, _in, expr: ast.LetIn(
        [(label, maybe_type, value)] + collect_many(more_lets, [1, 2, 4]),
        expr,
    ),
    # forall
    lambda _1, _2, label, _3, typ, _4, _5, expr: ast.ForAll(label, typ, expr),
    # arrow
    lambda a, _, b: ast.Arrow(a, b),
    identity,
]
actions['annotated-expression'] = [
    lambda _, a, b: ast.MergeExpression(a, b),
    lambda _1, a, b, _2, t: ast.TypeBound(ast.MergeExpression(a, b), t),

    lambda _1, _2, _3, _4, t: ast.TypeBound(ast.ListLiteral([]), ast.ListType(t)),
    lambda _1, _2, _3, _4, t: ast.TypeBound(ast.OptionalLiteral(None), ast.OptionalType(t)),
    lambda _1, e, _2, _3, _4, t: ast.TypeBound(ast.OptionalLiteral(e), ast.OptionalType(t)),

    lambda expr, _, typ: ast.TypeBound(expr, typ),
    identity,
]
actions['oprator-expression'] = [identity]

# operators
for name, wrapper in {
    # 'import-alt-expression': None,
    # 'or-expression': None,
    'plus-expression': ast.Plus,
    # 'text-append-expression': None,
    'list-append-expression': ast.ListAppendExpression,
    # 'and-expression': None,
    # 'combine-expression': None,
    # 'prefer-expression': None,
    # 'combine-types-expression': None,
    # 'times-expression': None,
    # 'equal-expression': None,
    # 'not-equal-expression': None,
    'application-expression': ast.ApplicationExpression,
}.items():
    actions[name] = [
        identity,
        _operator_wrapper(wrapper),
    ]

actions['constructors-or-some-expression'] = [
    # TODO
    # not_implemented_function('constructors'),
    # not_implemented_function('Some'),
    # identity,
    lambda a, b: (a, b) if a != [] else b,
]

actions['import-expression'] = [
    ast.ImportExpression,
    identity,
]

actions['selector-expression'] = [
    identity,
    lambda expr, _, label: ast.SelectExpression(expr, label),
    lambda expr, _1, _2: ast.ProjectionExpression(expr, []),
    lambda expr, _1, _2, label, labels, _3: ast.ProjectionExpression(expr, [label] + collect(labels, 1)),
]

actions['primitive-expression'] = [
    identity_list,
    identity_list,
    identity_list,

    # -infinity
    lambda _1, _2: float('-inf'),

    identity_list,

    # record type or literal
    lambda _1, a, _2: a,

    identity_list,
    identity_list,
    identity,  # identifier or builtin

    # ordinary parentesis
    lambda _1, a, _2: a,
]

actions['record-type-or-literal'] = [
    lambda _: ast.RecordLiteral({}),
    lambda: ast.RecordType({}),
    lambda label, _, e, c: ast.RecordType([(label, e)] + collect_many(c, [1, 3])),
    lambda label, _, e, c: ast.RecordLiteral([(label, e)] + collect_many(c, [1, 3])),
]

actions['non-empty-list-literal'] = [
    lambda _1, expr, exprs, _2: ast.ListLiteral([expr] + collect(exprs, 1)),
]

actions['builtin-or-identifier'] = [
    lambda a: ast.make_builtin_or_identifier(a),
    lambda a, _1, scope_num, _2: ast.Identifier(a, scope_num),
]


def _actions_wrapper(f):
    def wrapped(name, c):
        try:
            return f(*c)
        except TypeError as e:
            raise Exception('problem creating AST node {}'.format(name), e)
    return wrapped


_actions = {
    k: [_actions_wrapper(f) for f in v]
    for k, v in actions.items()
}

with timeit('making parser'):
    _grammar, _start = to_parglare_grammar(productions, terminals, original_start_symbol)
    assert _start == start_symbol
    parser = parglare.GLRParser(
        _grammar,
        ws='',
        table=parglare.tables.persist.table_from_serializable(parse_table, _grammar),
        actions=_actions,
    )


def load(filename):
    with open(filename, 'rt') as f:
        trees = parser.parse(f.read())
    assert len(trees) == 1  # GLR parser can return multiple trees when there is ambiguity
    return trees[0]
