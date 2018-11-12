from parglare_adapter import to_parglare_grammar
from parglare.tables import create_table, LALR
from parglare.tables.persist import table_to_serializable
from tools import timeit


def bnf2parglare(productions, terminals, original_start):
    grammar, start = to_parglare_grammar(productions, terminals, original_start)

    with timeit('computing parse table'):
        table = create_table(
            grammar,
            start_production=grammar.get_production_id(start),
            itemset_type=LALR,
            prefer_shifts=False,
            prefer_shifts_over_empty=False,
            lexical_disambiguation=False,
        )

    serializable_table = table_to_serializable(table)

    return productions, terminals, original_start, start, serializable_table


if __name__ == '__main__':
    import json
    import sys

    productions, terminals, original_start = json.load(sys.stdin)

    json.dump(
        bnf2parglare(productions, terminals, original_start),
        sys.stdout,
    )
