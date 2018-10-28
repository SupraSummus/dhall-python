import parglare
import sys
import re
import json

from tools import timeit


class EmptyTerminalsEliminator:
    __empty = None

    def __has_empty(self, args):
        return self.__empty in args

    def __no_empty(self, args):
        return [a for a in args if a != self.__empty]

    def sequence(self, args):
        return lark.Tree('sequence', self.__no_empty(args))

    def alternative(self, args):
        if self.__has_empty(args):
            return lark.Tree(
                'optional',
                [lark.Tree('alternative', self.__no_empty(args))],
            )
        else:
            return lark.Tree('alternative', args)


abnf_grammar_string = r"""
start: _? rules _? EOF;

hex_string: hex_string dot hex | hex;
dec_string: dec_string dot dec | dec;

string : "%x" hex_string
       | "%d" dec_string
       | "\"" quoted_string "\""
       ;

definition0 : definition0 _? "/" _? definition1
            | definition1
            ;
definition1 : definition1 _ definition2
            | definition2
            ;
definition2 : dec definition3
            | dec? "*" dec? definition3
            | definition3
            ;
definition3 : "(" _? definition0 _? ")"
            | "[" _? definition0 _? "]"
            | "%x" hex "-" hex
            | "%d" dec "-" dec
            | string
            | identifier
            ;

rule: identifier _? "=" _? definition0;
rules: rules _ rule
     | rule;

terminals
hex: /[0-9A-Fa-f]+/;
dec: /0|([1-9][0-9]*)/;
dot: ".";
quoted_string: /[^"]*/;
identifier: /[a-zA-Z][0-9a-zA-Z\-_]*/;
_: /([ \r\n\t]|;[^\r\n]*\r\n)+/;
"""
from pprint import pprint


def default(v, default):
    if v is None:
        return default
    else:
        return v


def take(name, indexes):
    def f(_, c):
        return (name, *(c[i] for i in indexes))
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
    abnf_grammar = parglare.Grammar.from_string(abnf_grammar_string)
    abnf_parser = parglare.GLRParser(
        abnf_grammar,
        ws=None,
        actions={
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
                lambda _, c: ('alternative', [c[0], c[4]]),
                take_raw(0),
            ],
            'definition1': [
                lambda _, c: ('sequence', [c[0], c[2]]),
                take_raw(0),
            ],
            'definition2': [
                take('exact_repetition', [0, 1]),
                take('range_repetition', [0, 2, 3]),
                take_raw(0),
            ],
            'definition3': [
                take_raw(2),
                take('optional', [2]),
                take('range', [1, 3]),
                take('range', [1, 3]),
                take('string', [0]),
                take('identifier', [0]),
            ],
            'rule': take('rule', [0, 4]),
            'rules': concat_0_2_actions,
            'start': take('rules', [1]),
        },
    )


def transformer(rules):
    def transform(tree):
        if isinstance(tree, tuple):
            return rules.get(
                tree[0],
                lambda *vs: (tree[0], *vs),
            )(*map(transform, list(tree[1:])))
        elif isinstance(tree, dict):
            return {
                k: transform(v)
                for k, v in tree.items()
            }
        elif isinstance(tree, list):
            return [
                transform(subtree)
                for subtree in tree
            ]
        else:
            return tree
    return transform


fix_names = transformer({
    'identifier': lambda s: ('identifier', s.replace('_', '__').replace('-', '_')),
    'rule': lambda s, d: ('rule', s.replace('_', '__').replace('-', '_'), d),
})


### convert grammar elements to supprted format


def fix_range_repetition(a, b, what):
    """Convert to 'a a a [a [a [a]]]'"""
    if a is None:
        a = 0

    # special cases
    if a == 1 and b is None:
        return ('one_or_more', what)
    if a == 0 and b is None:
        return ('zero_or_more', what)

    vs = [what] * a

    if b is None:
        vs.append(('zero_or_more', what))
    elif b - a > 0:
        nested = ('optional', what)
        for _ in range(b - a - 1):
            nested = ('optional', ('sequence', [what, nested]))
        vs.append(nested)

    return ('sequence', vs)


fix_repetitions = transformer({
    'range_repetition':fix_range_repetition,
    'exact_repetition': lambda n, c: ('sequence', [c] * n),
    'range': lambda a, b: ('regexp', '[{}-{}]'.format(
        re.escape(chr(a)),
        re.escape(chr(b)),
    ))
})


### squash nested alternatives and sequences

def squash(name):
    def f(vs):
        new_vs = []
        for v in vs:
            if isinstance(v, tuple) and v[0] == name:
                new_vs.extend(v[1])
            else:
                new_vs.append(v)
        return (name, new_vs)
    return f


optimize_conjuctive = transformer({
    'alternative': squash('alternative'),
    'sequence': squash('sequence'),
})



### flatten nested structures

def extract_anons(tree):
    anon_idents = {}  # content repr -> ident
    anons = {}  # ident -> content

    def get_ident(content):
        content_repr = repr(content)
        if content_repr not in anon_idents:
            anon_name = "__a{}".format(len(anons))
            anon_idents[content_repr] = anon_name
            anons[anon_name] = content
        return anon_idents[content_repr]

    def anon_extractor(name):
        def extract(vs):
            new_vs = []
            for v in vs:
                if v[0] in ('sequence', 'alternative'):
                    new_vs.append(('identifier', get_ident(v)))
                else:
                    new_vs.append(v)
            return (name, new_vs)
        return extract

    def single_anon_extractor(name):
        def extract(c):
            if c[0] in ('sequence', 'alternative'):
                new_c = ('identifier', get_ident(c))
            else:
                new_c = c
            return (name, new_c)
        return extract

    def append_anons(rules):
        new_rules = list(rules)
        for name, definition in anons.items():
            new_rules.append(('rule', name, definition))
        anons.clear()
        anon_idents.clear()
        return ('rules', new_rules)

    return transformer({
        'sequence': anon_extractor('sequence'),
        'optional': single_anon_extractor('optional'),
        'zero_or_more': single_anon_extractor('zero_or_more'),
        'one_or_more': single_anon_extractor('one_or_more'),
        'rules': append_anons,
    })(tree)



### extract terminals

def extract_terminals(tree):
    terminal_names = {}  # content -> ident
    terminals = {}  # ident -> content

    def get_ident(content):
        if content not in terminal_names:
            ident = '__t{}'.format(len(terminals))
            terminal_names[content] = ident
            terminals[ident] = content
        return terminal_names[content]

    def extract_string(v):
        if v == '':
            return ('string', v)
        else:
            return ('identifier', get_ident(('string', v)))

    def extract_regexp(v):
        return ('identifier', get_ident(('regexp', v)))

    def add_terminals(rules):
        return (
            'grammar',
            rules,
            [
                ('rule', k, v)
                for k, v in terminals.items()
            ],
        )

    return transformer({
        'string': extract_string,
        'regexp': extract_regexp,
        'rules': add_terminals,
    })(tree)

### grammar string construction ###


def make_parglare_grammar(grammar):
    return transformer({
        'grammar': lambda c, terminals: ''.join(c) + "\nterminals\n" + ''.join(terminals),
        'rule': lambda name, definition: name + ': ' + definition + ';\n',
        'alternative': lambda c: ' | '.join(c),
        'sequence': lambda c: ' '.join(c),
        'optional': lambda c: c + "?",
        'zero_or_more': lambda c: c + "*",
        'one_or_more': lambda c: c + "+",
        'identifier': lambda c: c,
        'string': lambda c: 'EMPTY' if c == '' else json.dumps(c),
        'regexp': lambda s: '/{}/'.format(s),
    })(grammar)


if __name__ == '__main__':
    with timeit('parsing the grammar'):
        trees = abnf_parser.parse(sys.stdin.read())
    assert len(trees) == 1
    tree = trees[0]

    tree = fix_names(tree)
    tree = fix_repetitions(tree)
    tree = optimize_conjuctive(tree)
    tree = extract_anons(tree)
    tree = extract_terminals(tree)
    
    #pprint(tree)
    #exit(0)
    
    tree = make_parglare_grammar(tree)
    print('__start: complete_expression EOF;')
    print(make_parglare_grammar(tree))
