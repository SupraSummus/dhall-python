.PHONY: all clean abnf_patch test

all: dhall/_grammar.py

clean:
	rm -rf dhall/_grammar.py dhall.abnf

dhall/_grammar.py: dhall.abnf abnf2bnf.py bnf2parglare.py json2python.py grammar_desugaring.py
	cat $< | python abnf2bnf.py complete-expression | python bnf2parglare.py | python json2python.py grammar > $@

dhall.abnf: dhall-lang/standard/dhall.abnf dhall.abnf.patch
	patch --binary -o $@ $^

abnf_patch:
	diff -u dhall-lang/standard/dhall.abnf dhall.abnf > dhall.abnf.patch

test: all
	cat dhall-haskell/tests/parser/annotations.dhall | python dhall.py
	cat dhall-haskell/tests/parser/builtins.dhall | python dhall.py
