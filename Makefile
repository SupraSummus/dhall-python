.PHONY: all clean abnf_patch test

all: dhall/grammar.py

clean:
	rm -rf dhall/grammar.py dhall.abnf

dhall/grammar.py: dhall.abnf abnf2parglare.py
	cat $< | python abnf2parglare.py > $@

dhall.abnf: dhall-lang/standard/dhall.abnf dhall.abnf.patch
	patch --binary -o $@ $^

abnf_patch:
	diff -u dhall-lang/standard/dhall.abnf dhall.abnf > dhall.abnf.patch

test: all
	cat dhall-haskell/tests/parser/annotations.dhall | python dhall.py
	cat dhall-haskell/tests/parser/builtins.dhall | python dhall.py
