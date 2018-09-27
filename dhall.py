import lark
import sys

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
