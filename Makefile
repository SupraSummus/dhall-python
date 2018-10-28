.PHONY: all clean abnf_patch test

all: dhall.parglare

clean:
	rm -rf dhall/_parser.py dhall.parglare dhall.abnf

dhall/_parser.py: dhall.lark
	python -m lark.tools.standalone $< complete_expression > $@

dhall.parglare: dhall.abnf abnf2parglare.py
	cat $< | python abnf2parglare.py > $@

dhall.abnf: dhall-lang/standard/dhall.abnf dhall.abnf.patch
	patch --binary -o $@ $^

abnf_patch:
	diff -u dhall-lang/standard/dhall.abnf dhall.abnf > dhall.abnf.patch

test: all
	cat tmp.dhall | python dhall.py
	cat dhall-haskell/tests/parser/annotations.dhall | python dhall.py
	cat dhall-haskell/tests/parser/builtins.dhall | python dhall.py
