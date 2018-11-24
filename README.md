Dhall for python
================

[![Build Status](https://travis-ci.com/SupraSummus/dhall-python.svg?branch=master)](https://travis-ci.com/SupraSummus/dhall-python)
[![codecov](https://codecov.io/gh/SupraSummus/dhall-python/branch/master/graph/badge.svg)](https://codecov.io/gh/SupraSummus/dhall-python)

Pure python implementation of [dhall](https://github.com/dhall-lang/dhall-lang) language.

**Work in progres**

    python setup.py build  # to patch the grammar and compile parser tables
    python setup.py test  # to run tests
    flake8  # to lint the code
    make abnf_patch  # to make changes to dhall.abnf persistent

Details:
 * parsing is done using [parglare](https://github.com/igordejanovic/parglare) GLR parser library
 * acceptance tests comes from dhall-lang repository

abnf2bnf.py
-----------

The scripts converts ABNF sugar into plain BNF-like format serialized in JSON. As an only argument it takes name of start symbol.

    cat dhall.abnf | python abnf2bnf.py complete-expression > dhall.bnf.json

bnf2parglare.py
----------------

This script will convert BNF grammar description into [parglare](https://github.com/igordejanovic/parglare) description.

    cat dhall.bnf.json | python bnf2parglare.py > dhall.parglare.json

dhall
-----

Dhall parser - work in progress

    cat dhall-haskell/tests/parser/annotations.dhall | python dhall.py
