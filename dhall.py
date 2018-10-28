import sys

import parglare
from tools import timeit


dhall_grammar = parglare.Grammar.from_file("dhall.parglare")
dhall_parser = parglare.GLRParser(dhall_grammar, ws='')


if __name__ == '__main__':
    with timeit('parsing'):
        tree = dhall_parser.parse(sys.stdin.read())

    from pprint import pprint
    pprint(tree)
