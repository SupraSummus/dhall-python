import sys

from tools import timeit
from dhall.parser import parser


if __name__ == '__main__':
    with timeit('parsing'):
        trees = parser.parse(sys.stdin.read())
    assert len(trees) == 1
    tree = trees[0]

    print(tree)
