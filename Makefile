all: dhall/_parser.py

clean:
	rm -rf dhall/_parser.py dhall.lark dhall.abnf

dhall/_parser.py: dhall.lark
	pipenv run python -m lark.tools.standalone $< complete_expression > $@

dhall.lark: dhall.abnf
	cat $< | pipenv run python abnf2lark.py > $@

dhall.abnf: dhall-lang/standard/dhall.abnf dhall.abnf.patch
	patch --binary -o $@ $^
