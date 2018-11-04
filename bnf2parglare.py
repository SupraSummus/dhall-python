if __name__ == '__main__':
    import json
    from dhall.parglare_adapter import to_parglare_grammar
    from parglare.tables import create_table, LALR
    from parglare.tables.persist import table_to_serializable
    import sys
    from tools import timeit

    productions, terminals, original_start = json.load(sys.stdin)
    grammar, start = to_parglare_grammar(productions, terminals, original_start)
    
    with timeit('computing parse table'):
        table = create_table(
            grammar,
            start_production=grammar.get_production_id(start),
            itemset_type=LALR,
            prefer_shifts=False,
            prefer_shifts_over_empty=False,
        )

    json.dump(
        (productions, terminals, original_start, start, table_to_serializable(table)),
        sys.stdout,
    )
