import lark
import sys

with open('dhall.lark') as f:
	parser = lark.Lark(
		f.read(),
		#parser='cyk',
		debug=True,
		lexer=None,
		ambiguity='explicit',
	)
