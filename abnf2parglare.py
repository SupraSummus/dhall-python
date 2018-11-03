import parglare
import sys

from tools import timeit
from dhall.parglare_adapter import to_parglare_grammar
from grammar_desugaring import (
    StringTerminal, RangeTerminal, Name,
    Sequence, Alternative, Optional, RangeRepetition, ExactRepetition,
    Grammar,
)

abnf_grammar, start_symbol = to_parglare_grammar(
    {
        'start': [['_?', 'rules', '_?']],
        'rules': [['rules', '_', 'rule'], ['rule']],
        'rule': [['identifier', '_?', '=', '_?', 'definition0']],

        'definition0': [
            ['definition0', '_?', '/', '_?', 'definition1'],
            ['definition1'],
        ],
        'definition1': [
            ['definition1', '_', 'definition2'],
            ['definition2'],
        ],
        'definition2': [
            ['dec', 'definition3'],
            ['dec?', '*', 'dec?', 'definition3'],
            ['definition3'],
        ],
        'definition3': [
            ['(', '_?', 'definition0', '_?', ')'],
            ['[', '_?', 'definition0', '_?', ']'],
            ['%x', 'hex', '-', 'hex'],
            ['%d', 'dec', '-', 'dec'],
            ['string'],
            ['identifier'],
        ],

        'hex_string': [['hex_string', 'dot', 'hex'], ['hex']],
        'dec_string': [['dec_string', 'dot', 'dec'], ['dec']],
        'string': [
            ['%x', 'hex_string'],
            ['%d', 'dec_string'],
            ['"', 'quoted_string', '"'],
        ],

        '_?': [['_'], []],
        'dec?': [['dec'], []],
    },
    {
        '*': ('string', '*'),
        '-': ('string', '-'),
        '_': ('regexp', r'([ \r\n\t]|;[^\r\n]*\r\n)+'),
        '=': ('string', '='),
        '"': ('string', '"'),
        '(': ('string', '('),
        ')': ('string', ')'),
        '/': ('string', '/'),
        '[': ('string', '['),
        ']': ('string', ']'),
        '%d': ('string', r'%d'),
        'dec': ('regexp', r'0|([1-9][0-9]*)'),
        'dot': ('string', '.'),
        'hex': ('regexp', r'[0-9A-Fa-f]+'),
        'identifier': ('regexp', r'[a-zA-Z][0-9a-zA-Z\-_]*'),
        'quoted_string': ('regexp', r'[^"]*'),
        '%x': ('string', r'%x'),
    },
    'start',
)


def default(v, default):
    if v is None:
        return default
    else:
        return v


def take(constructor, indexes):
    def f(_, c):
        return constructor(*(c[i] for i in indexes))
    return f


def take_raw(i):
    def f(_, c):
        return c[i]
    return f


concat_0_2_actions = [
    lambda _, c: c[0] + [c[2]],
    lambda _, c: c,
]


with timeit('making grammar parser'):

    abnf_parser = parglare.GLRParser(
        abnf_grammar,
        start_production=start_symbol,
        ws='',
        actions={
            'dec?': parglare.actions.optional,
            'hex?': parglare.actions.optional,
            'hex': lambda _, v: int(v, 16),
            'dec': lambda _, v: int(v, 10),
            'hex_string': concat_0_2_actions,
            'dec_string': concat_0_2_actions,
            'string': [
                lambda _, c: ''.join(map(chr, c[1])),
                lambda _, c: ''.join(map(chr, c[1])),
                take_raw(1),
            ],
            'definition0': [
                lambda _, c: Alternative((c[0], c[4])),
                take_raw(0),
            ],
            'definition1': [
                lambda _, c: Sequence((c[0], c[2])),
                take_raw(0),
            ],
            'definition2': [
                lambda _, c: ExactRepetition(c[0], c[1]),
                lambda _, c: RangeRepetition(c[3], c[0], c[2]),
                take_raw(0),
            ],
            'definition3': [
                take_raw(2),
                take(Optional, [2]),
                take(RangeTerminal, [1, 3]),
                take(RangeTerminal, [1, 3]),
                take(StringTerminal, [0]),
                take(Name, [0]),
            ],
            'rule': lambda _, c: (c[0], c[4]),
            'rules': concat_0_2_actions,
            'start': lambda _, c: Grammar(dict(c[1])),
            '__start': take_raw(0),
        },
    )

if __name__ == '__main__':
    from pprint import pprint

    with timeit('parsing the grammar'):
        trees = abnf_parser.parse(sys.stdin.read())
    assert len(trees) == 1
    tree = trees[0]

    productions, terminals = tree.to_productions_dict()
    print('grammar = ', end='')
    pprint((productions, terminals))
