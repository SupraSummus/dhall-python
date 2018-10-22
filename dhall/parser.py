from tools import timeit
from pprint import pprint

import os

DYNAMIC = bool(os.environ.get('DYNAMIC'))

if DYNAMIC:
    from lark import Discard, Transformer, Lark
    with timeit('making dynamic parser'):
        parser = Lark(
            open('dhall.lark').read(),
            parser='earley',
            #lexer="contextual",
            start='complete_expression',
            ambiguity='explicit',
        )

else:
    with timeit("importing parser"):
        from ._parser import Lark_StandAlone, Discard, Transformer
    with timeit('making parser'):
        parser = Lark_StandAlone()


def _inline_single(self, args):
    assert len(args) == 1, args
    return args[0]


def _inline_if_single(wrap=None):
    def f(self, args):
        if len(args) == 1:
            return args[0]
        elif wrap is None:
            return args
        else:
            return wrap(args)
    return f


#def _const(v):
#    def f(self, args):
#        assert len(args) == 0, args
#        return v
#    return f


def _discard(self, args):
    raise Discard()


class TreeNormalizer(Transformer):
    alpha = _inline_single
    comma = _discard
    colon = _discard
    open_brace = _discard
    close_brace = _discard
    open_angle = _discard
    close_angle = _discard
    open_parens = _discard
    close_parens = _discard
    whitespace = _discard
    whitespace_chunk = _discard

    import_alt_expression = _inline_if_single()
    or_expression = _inline_if_single()
    plus_expression = _inline_if_single()
    text_append_expression = _inline_if_single()
    list_append_expression = _inline_if_single()
    and_expression = _inline_if_single()
    combine_expression = _inline_if_single()
    prefer_expression = _inline_if_single()
    combine_types_expression = _inline_if_single()
    times_expression = _inline_if_single()
    equal_expression = _inline_if_single()
    not_equal_expression = _inline_if_single()
    annotated_expression = _inline_if_single()
    operator_expression = _inline_if_single()
    application_expression = _inline_if_single()
    import_expression = _inline_if_single()
    selector_expression = _inline_if_single()
    primitive_expression = _inline_single

    reserved = _inline_single
    reserved_raw = _inline_single
    record_type_or_literal = _inline_single
    complete_expression = _inline_single
    text_literal = _inline_single

    def simple_label(self, args):
        return ''.join(str(args))
