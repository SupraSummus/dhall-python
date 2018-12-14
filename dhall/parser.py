import re

import parglare

from . import ast
from .tools import timeit
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

actions['quoted-label'] = [concat_all]
actions['label'] = [lambda c, _ws: c if isinstance(c, str) else c[1]]

actions['natural-raw'] = [lambda f, c: int(f + ''.join(collect(c, 0)))]
actions['natural-literal'] = [lambda a, _: ast.NaturalLiteral(a)]
actions['double-literal'] = [lambda *a: ast.DoubleLiteral(float(concat_all(*a)))]

actions['double-quote-chunk'] = [
    lambda _1, expr, _2: expr,
    concat_all,
    identity,
    identity,
    identity,
    identity,
]
actions['double-quote-literal'] = [lambda _1, a, _2: ast.TextLiteral(collect(a, 0))]
actions['text-literal'] = [lambda a, _: a]

actions['path-component'] = [concat_all]
actions['query'] = [concat_all]
actions['fragment'] = [concat_all]
actions['scheme'] = [concat_all]
actions['authority'] = [
    concat_all,
    concat_all,
    concat_all,
]

actions['expression'] = [
    # lambda
    lambda _1, _2, label, _3, typ, _4, _5, expr: ast.Lambda(label, typ, expr),
    # conditional
    lambda _1, condition, _2, if_true, _3, if_false: ast.Conditional(condition, if_true, if_false),
    # let .. = .. in ..
    lambda _let, label, maybe_type, _eq, value, more_lets, _in, expr: ast.LetIn(
        [
            (l, v, None if len(t) == 0 else t[1])
            for l, v, t in [(label, value, maybe_type)] + collect_many(more_lets, [1, 4, 2])
        ],
        expr,
    ),
    # forall
    lambda _1, _2, label, _3, typ, _4, _5, expr: ast.ForAll(label, typ, expr),
    lambda a, _, b: ast.ForAll(ast.DEFAULT_VARIABLE_NAME, a, b),
    identity,
]
actions['annotated-expression'] = [
    lambda _, a, b: ast.MergeExpression(a, b),
    lambda _1, a, b, _2, t: ast.MergeExpression(a, b, t),

    lambda _1, _2, _3, _4, t: ast.TypeAnnotation(ast.ListLiteral([]), ast.ListType(t)),
    lambda _1, _2, _3, _4, t: ast.TypeAnnotation(ast.OptionalLiteral(), ast.OptionalType(t)),
    lambda _1, e, _2, _3, _4, t: ast.TypeAnnotation(ast.OptionalLiteral(e), ast.OptionalType(t)),

    lambda expr, _1, typ: ast.TypeAnnotation(expr, typ),
    identity,
]
actions['oprator-expression'] = [identity]

# operators
for name, wrapper in {
    # 'import-alt-expression': None,
    'or-expression': ast.Or,
    'plus-expression': ast.Plus,
    # 'text-append-expression': None,
    'list-append-expression': ast.ListAppendExpression,
    'and-expression': ast.And,
    # 'combine-expression': None,
    # 'prefer-expression': None,
    # 'combine-types-expression': None,
    'times-expression': ast.Times,
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
    # number literals
    identity,
    identity,
    identity,

    # -infinity
    lambda _1, _2: float('-inf'),

    # text literal
    identity,

    lambda _1, a, _2: a,  # record type or literal
    lambda _1, a, _2: a,  # union type or literal
    identity,  # nonempty list literal
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


def _make_nonempty_union_type_or_literal(c):
    label_and_value = None
    types = []

    while True:
        label, op, expr, tail = c
        op = op[0]
        if op == ':':
            types.append((label, expr))
            if tail == []:
                break
            else:
                c = tail[1]
        elif op == '=':
            label_and_value = (label, expr)
            types.extend(collect_many(tail, [1, 3]))
            break
        else:
            assert False

    if label_and_value is None:
        return ast.UnionType(types)
    else:
        return ast.Union(*label_and_value, types)


actions['union-type-or-literal'] = [
    _make_nonempty_union_type_or_literal,
    lambda: ast.UnionType([]),
]

actions['builtin-or-identifier'] = [
    lambda a: ast.make_builtin_or_variable(a),
    lambda a, _1, scope_num, _2: ast.Variable(a, scope_num),
]


def _actions_wrapper(f):
    def wrapped(name, c):
        try:
            return f(*c)
        except TypeError as e:
            raise Exception('problem creating AST node {}'.format(name), e)
    return wrapped


def simple_label_recognizer(text, pos):
    """detect simple labels by regexp, then reject keywords"""
    match = re.match(r'[A-Za-z_][0-9A-Za-z\-/_]*', text[pos:])
    if match is None:
        return None
    else:
        name = match.group(0)
    if name in [
        'forall',
        'if', 'then', 'else',
        'let', 'in',
        'missing', 'as',
        'constructors', 'Some', 'merge',
    ]:
        return None
    return name


single_quote_regular_chunk_recognizer = parglare.RegExRecognizer(
    r'''(
        ''\${  |  # escaped interpolation sequence
        \$[^{']|  # $, but not an interpolation one
        [^\$'] |  # anything but not a $ or '
        \'\'\'    # escaped '
    )+''',
    name='single-quote-regular-chunk',
    re_flags=re.VERBOSE | re.MULTILINE,
)

_actions = {
    k: [_actions_wrapper(f) for f in v]
    for k, v in actions.items()
}

with timeit('making parser'):
    _grammar, _start = to_parglare_grammar(
        productions, terminals, original_start_symbol,
        recognizers={
            'simple-label': simple_label_recognizer,
            'single-quote-regular-chunk': single_quote_regular_chunk_recognizer,
        },
    )
    assert _start == start_symbol
    parser = parglare.GLRParser(
        _grammar,
        ws='',
        table=parglare.tables.persist.table_from_serializable(parse_table, _grammar),
        actions=_actions,
    )


class SyntaxError(Exception):
    pass


def parse(string):
    try:
        trees = parser.parse(string)
    except parglare.ParseError as e:
        raise SyntaxError(e)
    # GLR parser can return multiple trees when there is ambiguity
    assert len(trees) == 1, "Ambiguity detected - got {} parses".format(len(trees))
    return trees[0]


def load(filename):
    with open(filename, 'rt') as f:
        return parse(f.read())
