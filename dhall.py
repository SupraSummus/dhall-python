import sys

from dhall.parser import parser, TreeNormalizer
from tools import timeit


if __name__ == '__main__':
    with timeit('parsing'):
        tree = parser.parse(sys.stdin.read())

    tree = TreeNormalizer().transform(tree)
    print(tree.pretty())
