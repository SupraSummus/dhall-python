import sys

from tools import timeit
from dhall.parser import parser


if __name__ == '__main__':
    with timeit('parsing'):
        tree = parser.parse(sys.stdin.read())

    from pprint import pprint
    pprint(tree)
