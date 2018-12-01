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

Status
------

 * [x] parsing

   All tests from acceptance test suite pass, except AST is not checked against CBOR.
 
 * [ ] typechecking / evaluating / normalizing

   Some tests from acceptance test suite pass, but typechecking infrastructure needs to be havily reworked.

 * [ ] import resolution
 * [ ] loading from / dumping to binary
 * [ ] (pretty)printing expressions
 
   There is some code responsible for printing for type errors explanation, but it's incomplete and does not properly support precedence.

Details
-------

Parsing is done using [parglare](https://github.com/igordejanovic/parglare) GLR parser library. `grammar.abnf` from dhall-lang repository is first patched, then converted into GLR parser tables. Take a look at [`setup.py`](setup.py), how it's done.

Acceptance tests comes from dhall-lang repository. They are then triggered during unit testing using awesome [parametrized package](https://github.com/wolever/parameterized). Take a look at [`tests/test_acceptance.py`](tests/test_acceptance.py).

To check what dhall-python is capable of parsing call something like

    cat dhall-haskell/tests/parser/annotations.dhall | dhall-python-parse
