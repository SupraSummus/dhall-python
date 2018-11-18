from dataclasses import dataclass, field
from typing import Generic, TypeVar, Dict, Sequence, Tuple

from pyrsistent import pvector

KT = TypeVar('KT')
VT = TypeVar('VT')


@dataclass(frozen=True)
class ShadowDict(Generic[KT, VT]):
    """An immutable dict that rememers all inserted values, even if they
    were shadowed (overwritten) later. Immutable dict remembers also age of
    each insertion."""
    entries: Dict[KT, Sequence[Tuple[VT, int]]] = field(default_factory=dict)
    generation: int = 0

    def shadow(self, entries: Dict[KT, VT]) -> 'ShadowDict[KT, VT]':
        new_generation = self.generation + 1
        new_entries = {n: vs for n, vs in self.entries.items()}
        for n, v in entries.items():
            new_entries[n] = new_entries.get(n, pvector()).append((v, new_generation))
        return ShadowDict(new_entries, new_generation)

    def has(self, name: KT, scope: int = 0) -> bool:
        return len(self.entries.get(name, [])) > scope

    def get(self, name: KT, scope: int = 0) -> VT:
        return self.entries.get(name, pvector())[-scope - 1][0]

    def age(self, name: KT, scope: int = 0) -> int:
        return self.generation - self.entries.get(name, pvector())[-scope - 1][1]
