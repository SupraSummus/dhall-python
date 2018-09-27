import lark
import sys

from pprint import pprint


class TreeNormalizer(lark.Transformer):
    def not_end_of_line(self, args):
        assert len(args) == 1
        return args[0]

    def end_of_line(self, args):
        assert len(args) == 0
        return '\n'

    def whitespace_chunk(self, args):
        if len(args) == 1:
            return args[0]
        elif len(args) == 0:
            return ''
        else:
            assert False, args

    def alpha(self, args):
        assert len(args) == 1
        return args[0]

    def simple_label(self, args):
        return lark.Tree('label', [''.join(args)])

    def line_comment(self, args):
        return lark.Tree('comment', [''.join(args)])


if __name__ == '__main__':
    with open('dhall.lark') as f:
        grammar = f.read()

    parser = lark.Lark(
        grammar,
        #parser='cyk',
        debug=True,
        #lexer=None,
        ambiguity='explicit',
        start='complete_expression',
    )

    tree = parser.parse(sys.stdin.read())
    tree = TreeNormalizer().transform(tree)
    print(tree.pretty())
