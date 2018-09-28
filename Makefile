all: dhall/_parser.py

clean:
	rm -rf dhall/_parser.py dhall/_dhall.lark

dhall/_parser.py: dhall/_dhall.lark
	pipenv run python -m lark.tools.standalone $< complete_expression > $@

dhall/_dhall.lark: dhall/dhall.abnf
	cat $< | pipenv run python abnf2lark.py > $@
