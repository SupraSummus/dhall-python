**Work in progres**

    make test

abnf2parglare.py
----------------

This script will convert ABNF grammar description into [parglare](https://github.com/igordejanovic/parglare) description.

    cat dhall/dhall.abnf | python abnf2parglare.py > dhall.parglare

This is currently not working fully. Regexp terminals are not fully escaped.

dhall
-----

Dhall parser - work in progress

    cat example.dhall | python dhall.py
