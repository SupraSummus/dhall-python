.PHONY: all clean abnf_patch test

all: dhall/_parser.py

clean:
	rm -rf dhall/_parser.py dhall.lark dhall.abnf

dhall/_parser.py: dhall.lark
	pipenv run python -m lark.tools.standalone $< complete_expression > $@

dhall.lark: dhall.abnf
	cat $< | pipenv run python abnf2lark.py > $@

dhall.abnf: dhall-lang/standard/dhall.abnf dhall.abnf.patch
	patch --binary -o $@ $^

abnf_patch:
	diff -u dhall-lang/standard/dhall.abnf dhall.abnf > dhall.abnf.patch

test: all
	cat dhall-haskell/tests/parser/annotations.dhall | pipenv run python dhall.py
	cat dhall-haskell/tests/parser/builtins.dhall | pipenv run python dhall.py
