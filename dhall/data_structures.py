from typing import Generic, TypeVar, Dict, Sequence, Tuple

import attr
from pyrsistent import pvector

KT = TypeVar('KT')
VT = TypeVar('VT')


@attr.s(frozen=True, auto_attribs=True)
class ShadowDict(Generic[KT, VT]):
    """An immutable dict that rememers all inserted values, even if they
    were shadowed (overwritten) later. Immutable dict remembers also age of
    each insertion."""
    entries: Dict[KT, Sequence[Tuple[VT, int]]]
    entries = attr.ib(default=attr.Factory(dict))
    generation: int = 0

    def shadow(self, entries: Dict[KT, VT]) -> 'ShadowDict[KT, VT]':
        # TODO improve complexity, as it's now O(#variables) - too bad
        new_generation = self.generation + 1
        new_entries = {n: vs for n, vs in self.entries.items()}
        for n, v in entries.items():
            new_entries[n] = new_entries.get(n, pvector()).append((v, new_generation))
        return ShadowDict(new_entries, new_generation)

    def shadow_single(self, name, value):
        return self.shadow({name: value})

    def join(self, other):
        entries = dict(self.entries)
        for k, vs in other.entries.items():
            old_vs = entries.get(k, pvector())
            entries[k] = old_vs + vs
        return ShadowDict(entries, self.generation)

    def has(self, name: KT, scope: int = 0) -> bool:
        return len(self.entries.get(name, [])) > scope

    def get(self, name: KT, scope: int = 0) -> VT:
        return self.entries.get(name, pvector())[-scope - 1][0]

    def age(self, name: KT, scope: int = 0) -> int:
        return self.generation - self.entries.get(name, pvector())[-scope - 1][1]

    def map(self, f):
        return ShadowDict(
            {
                k: pvector([(f(v), g) for v, g in vs])
                for k, vs in self.entries.items()
            },
            self.generation,
        )

    def pretty_string(self, f):
        if self.entries:
            return '\n'.join([
                '{}: {}'.format(k, tuple(f(v[0]) for v in vs))
                for k, vs in self.entries.items()
            ])
        else:
            return '<empty>'

    def __str__(self):
        return self.pretty_string(str)
