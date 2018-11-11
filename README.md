Dhall for python
================

[![Build Status](https://travis-ci.com/SupraSummus/python-dhall.svg?branch=master)](https://travis-ci.com/SupraSummus/python-dhall)

Pure python implementation of dhall language.

**Work in progres**

    make test


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
