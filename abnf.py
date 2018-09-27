import lark
import sys
import re
import json

class ABNFNormalizer(lark.Transformer):
	def hex(self, args):
		return int(args[0], base=16)

	def dec(self, args):
		return int(args[0], base=10)

	def empty_string(self, args):
		return ''

	def numeric_sequence(self, args):
		return ''.join(map(chr, args))

	def unbound_repetition_spec(self, args):
		if len(args) == 0:
			return 0
		else:
			return args[0]

	def repetition_high_bound(self, args):
		if len(args) == 1:
			return [0, args[0]]
		else:
			return args

	def repetition_exact(self, args):
		return [args[0], args[0]]


def indent(s, indent='  '):
	return '{}{}'.format(
		indent,
		s.replace('\n', '\n' + indent),
	)


class MakeLarkGrammar(lark.Transformer):
	def start(self, args):
		return ''.join(args)

	def rule(self, args):
		return '{}: {}\n'.format(args[0], args[1])

	def sequence(self, args):
		return '({})'.format(' '.join(args))

	def alternative(self, args):
		return '({})'.format(' | '.join(args))

	def identifier(self, args):
		return args[0].replace('-', '_').lower()

	def string(self, args):
		return json.dumps(args[0])

	def range(self, args):
		return '/[{}-{}]/'.format(
			re.escape(chr(args[0])),
			re.escape(chr(args[1])),
		)

	def unbound_repetition(self, args):
		r = []
		for _ in range(args[0]):
			r.append(args[1])
		r.append(args[1] + '*')
		return '({})'.format(' '.join(r))

	def bound_repetition(self, args):
		r = []
		for _ in range(args[0][0]):
			r.append(args[1])
		for _ in range(args[0][1] - args[0][0]):
			r.append('[{}]'.format(args[1]))
		return '({})'.format(' '.join(r))

	def optional(self, args):
		return '[{}]'.format(args[0])


if __name__ == '__main__':
	with open('abnf.lark') as f:
		parser = lark.Lark(
			f.read(),
			parser='earley',
			debug=True,
			lexer='dynamic',
			ambiguity='explicit',
		)

	tree = parser.parse(sys.stdin.read())

	tree = ABNFNormalizer().transform(tree)

	print(MakeLarkGrammar().transform(tree))
