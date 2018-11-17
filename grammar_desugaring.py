from collections import namedtuple
import re


class DesugaringError(Exception):
    pass


class Empty:
    def to_productions(self, builder):
        return ((),)

    def as_dict(self):
        return {
            'type': 'empty',
        }


class StringTerminal(namedtuple('StringTerminal', ('string',))):
    def to_productions(self, builder):
        if self.string == '':
            return Empty().to_productions(builder)
        else:
            string = ('string', self.string)
            return ((builder.store_terminal(string),),)

    def as_dict(self):
        return {
            'type': 'string',
            'string': self.string,
        }


class RangeTerminal(namedtuple('StringTerminal', ('min', 'max'))):
    def to_productions(self, builder):
        regexp = ('regexp', '[{}-{}]'.format(
            re.escape(chr(self.min)),
            re.escape(chr(self.max)),
        ))
        return ((builder.store_terminal(regexp),),)

    def as_dict(self):
        return {
            'type': 'range_terminal',
            'min': self.min,
            'max': self.max,
        }


class Name(namedtuple('Name', ('name',))):
    def to_productions(self, builder):
        return ((self.name,),)

    def as_dict(self):
        return {
            'type': 'name',
            'name': self.name,
        }


class Optional(namedtuple('Optional', ('child',))):
    def to_productions(self, builder):
        return Alternative((self.child, Empty())).to_productions(builder)

    def as_dict(self):
        return {
            'type': 'optional',
            'child': self.child.as_dict(),
        }


class ExactRepetition(namedtuple('ExactRepetition', ('count', 'child'))):
    def to_productions(self, builder):
        return Sequence((self.child,) * self.count).to_productions(builder)

    def as_dict(self):
        return {
            'type': 'exact_repetition',
            'count': self.count,
            'child': self.child.as_dict(),
        }


class RangeRepetition:
    def __init__(self, child, min_count=None, max_count=None):
        if min_count is None:
            min_count = 0
        assert (max_count is None) or (min_count <= max_count)
        self.child = child
        self.min = min_count
        self.max = max_count

    def to_productions(self, builder):
        """Convert to 'a a a [[[a] a] a]' or 'a a a a*'"""
        if self.max is None:
            looping_rule_name = builder.new_anonymous_name()
            looping_rule = Name(looping_rule_name)
            builder.store_productions(
                Alternative((
                    Empty(),
                    Sequence((looping_rule, self.child)),
                )).to_productions(builder),
                looping_rule_name,
            )
            tail = looping_rule

        elif self.max - self.min > 0:
            tail = Optional(self.child)
            for _ in range(self.max - self.min - 1):
                tail = Optional(Sequence(
                    (tail, self.child),
                ))

        return Sequence((self.child,) * self.min + (tail,)).to_productions(builder)

    def as_dict(self):
        return {
            'type': 'range_repetition',
            'min': self.min,
            'max': self.max,
            'child': self.child.as_dict(),
        }


class Alternative(namedtuple('Alternative', ('children',))):
    def to_productions(self, builder):
        productions = []
        for child in self.children:
            productions.extend(child.to_productions(builder))
        return tuple(productions)

    def as_dict(self):
        return {
            'type': 'alternative',
            'children': [c.as_dict() for c in self.children],
        }


class Sequence(namedtuple('Sequence', ('children',))):
    def to_productions(self, builder):
        production = []
        for child in self.children:
            cp = child.to_productions(builder)
            if len(cp) == 1:
                production.extend(cp[0])
            else:
                name = builder.store_productions(cp)
                production.append(name)
        return (tuple(production),)

    def as_dict(self):
        return {
            'type': 'sequence',
            'children': [c.as_dict() for c in self.children],
        }


class ProductionsBuilder:
    def __init__(self):
        self.productions_dict = {}  # name -> productions
        self.names = {}  # productions -> name
        self.anonymous_count = 0

        self.terminals = {}  # name -> terminal definition
        self.terminal_names = {}  # terminal definition -> name

    def new_anonymous_name(self):
        name = "__a{}".format(self.anonymous_count)
        self.anonymous_count += 1
        return name

    def store_productions(self, productions, name=None):
        if name is None:
            if productions in self.names:
                return self.names[productions]
            else:
                name = self.new_anonymous_name()
        if name in self.productions_dict:
            raise DesugaringError("production for symbol {} are already defined".format(name))
        if productions in self.names and productions != ((),):
            raise DesugaringError(
                "productions {} are already stored under name {} (trying to store them as {})".format(
                    productions,
                    self.names[productions],
                    name,
                ),
            )
        self.productions_dict[name] = productions
        self.names[productions] = name
        return name

    def store_terminal(self, definition):
        if definition not in self.terminal_names:
            name = "__t{}".format(len(self.terminals))
            assert definition not in self.terminal_names
            assert name not in self.terminals
            self.terminal_names[definition] = name
            self.terminals[name] = definition
        return self.terminal_names[definition]


class Grammar:
    def __init__(self, rules):
        self.rules = rules

    def to_productions_dict(self):
        builder = ProductionsBuilder()

        for name, definition in self.rules.items():
            builder.store_productions(definition.to_productions(builder), name)

        return builder.productions_dict, builder.terminals

    def as_dict(self):
        return {k: v.as_dict() for k, v in self.rules.items()}
