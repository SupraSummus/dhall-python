import parglare


def to_parglare_grammar(productions_dict, terminals_dict, start, **kwargs):
    """Make parglare Grammar object from plain description dicts.
     * productions_dict is a dictionary mapping nonterminal names into list of alternative productions equences
     * terminals_dict is a dictionary mapping terminal names into their definition

    Example. A grammar for strings containg a, b and c multiple times:
    to_parglare_grammar(
        {
            'start': [['start', 'a'], ['start', 'b_or_c'], []],
        },
        {
            'a': ('string', 'a'),
            'b_or_c': ('regexp', 'b|c'),
        },
        'start',
    )
    """
    def make_terminal(name, t):
        typ = t[0]
        if typ == 'external':
            return parglare.Terminal(name=name)

        val = t[1]
        if typ == 'string':
            recognizer_class = parglare.StringRecognizer
        elif typ == 'regexp':
            recognizer_class = parglare.RegExRecognizer
        else:
            assert False
        return parglare.Terminal(recognizer=recognizer_class(val), name=name)

    terminals = {
        name: make_terminal(name, value)
        for name, value in terminals_dict.items()
    }

    non_terminals = {
        name: parglare.NonTerminal(name)
        for name in productions_dict.keys()
    }

    def get_symbol(name):
        if name in terminals:
            assert name not in non_terminals
            return terminals[name]
        else:
            return non_terminals[name]

    productions = []
    for name, alternatives in productions_dict.items():
        for alternative in alternatives:
            symbol = non_terminals[name]
            rhs = parglare.grammar.ProductionRHS([get_symbol(s) for s in alternative])
            productions.append(parglare.grammar.Production(
                symbol,
                rhs,
            ))

    start_non_terminal = parglare.NonTerminal('__start')
    productions.append(parglare.grammar.Production(
        start_non_terminal,
        parglare.grammar.ProductionRHS([non_terminals[start], parglare.EOF]),
    ))

    return parglare.Grammar(
        productions=productions,
        terminals=terminals.values(),
        start_symbol=start_non_terminal,
        **kwargs,
    ), '__start'
