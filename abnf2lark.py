import lark
import sys
import re
import json

class ABNFNormalizer(lark.Transformer):
    def hex(self, args):
        assert len(args) == 1
        return int(args[0], base=16)

    def dec(self, args):
        assert len(args) == 1
        return int(args[0], base=10)

    def empty_string(self, args):
        assert len(args) == 0
        return ''

    def numeric_sequence(self, args):
        return ''.join(map(chr, args))

    def just_a_string(self, args):
        """Convert Token to plain string"""
        assert len(args) == 1
        return str(args[0])

    def unbound_repetition_spec(self, args):
        assert len(args) <= 1
        if len(args) == 0:
            return 0
        else:
            return args[0]

    def repetition_high_bound(self, args):
        assert len(args) <= 2
        if len(args) == 1:
            return [0, args[0]]
        else:
            return args

    def repetition_exact(self, args):
        assert len(args) == 1
        return [args[0], args[0]]


class EmptyTerminalsEliminator(lark.Transformer):
    __empty = lark.Tree('string', [''])

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


class MakeLarkGrammar(lark.Transformer):
    def start(self, args):
        return ''.join(args)

    def rule(self, args):
        assert len(args) == 2
        return '{}: {}\n'.format(args[0], args[1])

    def sequence(self, args):
        return '({})'.format(' '.join(args))

    def alternative(self, args):
        return '({})'.format(' | '.join(args))

    def identifier(self, args):
        assert len(args) == 1
        return args[0].replace('-', '_').lower()

    def string(self, args):
        assert len(args) == 1
        return json.dumps(args[0])

    def range(self, args):
        assert len(args) == 2
        return '/[{}-{}]/'.format(
            re.escape(chr(args[0])),
            re.escape(chr(args[1])),
        )

    def unbound_repetition(self, args):
        """Convert to 'a a a a*'"""
        assert len(args) == 2
        r = []
        for _ in range(args[0]):
            r.append(args[1])
        r.append(args[1] + '*')
        return '({})'.format(' '.join(r))

    def bound_repetition(self, args):
        """Convert to 'a a a [a] [a]'"""
        assert len(args) == 2
        assert len(args[0]) == 2
        r = []
        for _ in range(args[0][0]):
            r.append(args[1])
        for _ in range(args[0][1] - args[0][0]):
            r.append('[{}]'.format(args[1]))
        return '({})'.format(' '.join(r))

    def optional(self, args):
        assert len(args) == 1
        return '[{}]'.format(args[0])


if __name__ == '__main__':
    with open('abnf.lark') as f:
        grammar = f.read()

    parser = lark.Lark(
        grammar,
        parser='earley',
        debug=True,
        lexer='dynamic',
        ambiguity='explicit',
    )

    tree = parser.parse(sys.stdin.read())
    tree = ABNFNormalizer().transform(tree)
    tree = EmptyTerminalsEliminator().transform(tree)
    print(MakeLarkGrammar().transform(tree))
