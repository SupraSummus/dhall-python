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


def collect_pairs(c, a_index, b_index):
    pairs = []
    # increase by 1 to account for the first, recursive segment
    a_index += 1
    b_index += 1
    while len(c) != 0:
        pairs.append((c[a_index], c[b_index]))
        c = c[0]
    pairs.reverse()
    return pairs


def not_implemented_function(text=None):
    def f(*args, **kwargs):
        raise NotImplementedError(text)
    return f


actions = {}

actions[start_symbol] = [lambda a, _: a]
actions[original_start_symbol] = [lambda _, a: a]

actions['simple-label'] = [concat_all]
actions['quoted-label'] = [concat_all]
actions['label'] = [lambda c, _ws: c if isinstance(c, str) else c[1]]

actions['expression'] = [
    # lambda
    lambda _1, _2, label, _3, typ, _4, _5, expr: ast.Lambda(label, typ, expr),
    # conditional
    lambda _1, condition, _2, if_true, _3, if_false: ast.Conditional(condition, if_true, if_false),
    # let .. = .. in ..
    lambda _1, label, maybe_type, _2, value, _3, expr: ast.LetIn(label, maybe_type, value, expr),
    # forall
    lambda _1, _2, label, _3, typ, _4, _5, expr: ast.ForAll(label, typ, expr),
    # arrow
    lambda a, _, b: ast.Arrow(a, b),
    identity,
]
actions['annotated-expression'] = [
    identity_list,
    identity_list,
    lambda expr, maybe_type: ast.TypeBound(expr, maybe_type[1]) if len(maybe_type) > 0 else expr,
]
actions['oprator-expression'] = [identity]

for name, wrapper in {
    'import-alt-expression': None,
    'or-expression': None,
    'plus-expression': None,
    'text-append-expression': None,
    'list-append-expression': ast.ListAppendExpression,
    'and-expression': None,
    'combine-expression': None,
    'prefer-expression': None,
    'combine-types-expression': None,
    'times-expression': None,
    'equal-expression': None,
    'not-equal-expression': None,
    'application-expression': ast.ApplicationExpression,
    'selector-expression': ast.SelectorExpression,
}.items():
    actions[name] = [
        identity,
        {
            True: not_implemented_function('expression {} not implemented'.format(name)),
            False: lambda *c: wrapper(c[0], c[-1]),
        }[wrapper is None],
    ]

actions['constructors-or-some-expression'] = [
    # TODO
    # not_implemented_function('constructors'),
    # not_implemented_function('Some'),
    # identity,
    lambda _, a: a,
]

actions['import-expresstion'] = [
    ast.ImportExpression,
    identity,
]

actions['primitive-expression'] = [
    identity,
    identity,
    identity,
    identity,
    # record type or literal
    lambda _1, a, _2: a,
    identity,
    identity,
    identity,
    identity,
    identity,
    identity,
    identity,
    # ordinary parentesis
    lambda _1, a, _2: a,
]

actions['record-type-or-literal'] = [
    lambda _: ast.RecordLiteral({}),
    lambda _: ast.RecordType({}),
    lambda label, _, e, c: ast.RecordType([(label, e)] + collect_pairs(c, 1, 3)),
    lambda label, _, e, c: ast.RecordLiteral([(label, e)] + collect_pairs(c, 1, 3)),
]


def _actions_wrapper(f):
    def wrapped(_, c):
        return f(*c)
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
