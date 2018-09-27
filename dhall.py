import lark
import sys

from pprint import pprint


def _inline_single(self, args):
    assert len(args) == 1, args
    return args[0]

def _inline_if_single(wrap=None):
    def f(self, args):
        if len(args) == 1:
            return args[0]
        else:
            return wrap(args)
    return f

def _const(v):
    def f(self, args):
        assert len(args) == 0, args
        return v
    return f

def _discard(self, args):
    raise lark.Discard()


class TreeNormalizer(lark.Transformer):
    alpha = _inline_single
    comma = _discard
    colon = _discard
    open_brace = _discard
    close_brace = _discard
    open_angle = _discard
    close_angle = _discard
    whitespace = _discard

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

    def simple_label(self, args):
        return ''.join(args)


if __name__ == '__main__':
    with open('dhall.lark') as f:
        grammar = f.read()

    parser = lark.Lark(
        grammar,
        #parser='cyk',
        debug=True,
        #lexer=None,
        ambiguity='explicit',
        start='complete_expression',
    )

    tree = parser.parse(sys.stdin.read())
    tree = TreeNormalizer().transform(tree)
    print(tree.pretty())
