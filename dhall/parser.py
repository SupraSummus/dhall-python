from tools import timeit
import parglare

from .ast import (
    Lambda, Conditional, LetIn, ForAll, Arrow,
    TypeBound,
    ListAppendExpression,
)
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


def pass_single_and_wrap_more(wrapper):
    def f(first, nexts):
        if nexts == []:
            return first
        else:
            return wrapper([first] + nexts)
    return [f]


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
    lambda _1, _2, label, _3, typ, _4, _5, expr: Lambda(label, typ, expr),
    # conditional
    lambda _1, condition, _2, if_true, _3, if_false: Conditional(condition, if_true, if_false),
    # let .. = .. in ..
    lambda _1, label, maybe_type, _2, value, _3, expr: LetIn(label, maybe_type, value, expr),
    # forall
    lambda _1, _2, label, _3, typ, _4, _5, expr: ForAll(label, typ, expr),
    # arrow
    lambda a, _, b: Arrow(a, b),
    identity,
]
actions['annotated-expression'] = [
    identity_list,
    identity_list,
    lambda expr, maybe_type: TypeBound(expr, maybe_type[1]) if len(maybe_type) > 0 else expr,
]
actions['oprator-expression'] = [parglare.actions.pass_single]
for name, wrapper in {
    'import-alt-expression': None,
    'or-expression': None,
    'plus-expression': None,
    'text-append-expression': None,
    'list-append-expression': ListAppendExpression,
    'and-expression': None,
    'combine-expression': None,
    'prefer-expression': None,
    'combine-types-expression': None,
    'times-expression': None,
    'equal-expression': None,
    'not-equal-expression': None,
}.items():
    actions[name] = pass_single_and_wrap_more(
        not_implemented_function('expression {} not implemented'.format(name)) if wrapper is None else wrapper,
    )

actions['application-expression'] = [
    lambda _, expr, tail: ('application', _, expr, tail) if len(tail) > 0 else expr,
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
