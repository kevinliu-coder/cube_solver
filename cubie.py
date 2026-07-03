"""Cubie-level model of the 3x3 cube (Kociemba conventions).

Corners (0..7): URF UFL ULB UBR DFR DLF DBL DRB
Edges   (0..11): UR UF UL UB DR DF DL DB FR FL BL BR

State = (cp, co, ep, eo)
  cp[i] = which corner cubie sits in slot i
  co[i] = its orientation (0,1,2) measured as CW twists of the U/D facelet
  ep[i] = which edge cubie sits in slot i
  eo[i] = its orientation (0,1)

Move composition: applying move M to state A gives A * M, i.e. M is applied
"after" the current arrangement. This is the standard right-action used by
Kociemba's coordinate solver.
"""
from __future__ import annotations
from dataclasses import dataclass, field

# corner / edge names for pretty printing
CORNER_NAMES = ["URF", "UFL", "ULB", "UBR", "DFR", "DLF", "DBL", "DRB"]
EDGE_NAMES = ["UR", "UF", "UL", "UB", "DR", "DF", "DL", "DB", "FR", "FL", "BL", "BR"]


@dataclass
class CubieCube:
    cp: list[int] = field(default_factory=lambda: list(range(8)))
    co: list[int] = field(default_factory=lambda: [0] * 8)
    ep: list[int] = field(default_factory=lambda: list(range(12)))
    eo: list[int] = field(default_factory=lambda: [0] * 12)

    def copy(self) -> "CubieCube":
        return CubieCube(self.cp[:], self.co[:], self.ep[:], self.eo[:])

    # ---- composition: self * other ----
    def corner_multiply(self, o: "CubieCube") -> None:
        cp, co = [0] * 8, [0] * 8
        for i in range(8):
            cp[i] = self.cp[o.cp[i]]
            co[i] = (self.co[o.cp[i]] + o.co[i]) % 3
        self.cp, self.co = cp, co

    def edge_multiply(self, o: "CubieCube") -> None:
        ep, eo = [0] * 12, [0] * 12
        for i in range(12):
            ep[i] = self.ep[o.ep[i]]
            eo[i] = (self.eo[o.ep[i]] + o.eo[i]) % 2
        self.ep, self.eo = ep, eo

    def multiply(self, o: "CubieCube") -> None:
        self.corner_multiply(o)
        self.edge_multiply(o)

    def is_solved(self) -> bool:
        return (self.cp == list(range(8)) and self.co == [0] * 8
                and self.ep == list(range(12)) and self.eo == [0] * 12)

    def __eq__(self, o) -> bool:
        return (self.cp == o.cp and self.co == o.co
                and self.ep == o.ep and self.eo == o.eo)


# ---- the six face quarter-turn generators ----
def _mk(cp, co, ep, eo) -> CubieCube:
    return CubieCube(cp, co, ep, eo)

MOVE_CUBES = {
    "U": _mk([3, 0, 1, 2, 4, 5, 6, 7], [0]*8,
             [3, 0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11], [0]*12),
    "R": _mk([4, 1, 2, 0, 7, 5, 6, 3], [2, 0, 0, 1, 1, 0, 0, 2],
             [8, 1, 2, 3, 11, 5, 6, 7, 4, 9, 10, 0], [0]*12),
    "F": _mk([1, 5, 2, 3, 0, 4, 6, 7], [1, 2, 0, 0, 2, 1, 0, 0],
             [0, 9, 2, 3, 4, 8, 6, 7, 1, 5, 10, 11], [0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0]),
    "D": _mk([0, 1, 2, 3, 5, 6, 7, 4], [0]*8,
             [0, 1, 2, 3, 5, 6, 7, 4, 8, 9, 10, 11], [0]*12),
    "L": _mk([0, 2, 6, 3, 4, 1, 5, 7], [0, 1, 2, 0, 0, 2, 1, 0],
             [0, 1, 10, 3, 4, 5, 9, 7, 8, 2, 6, 11], [0]*12),
    "B": _mk([0, 1, 3, 7, 4, 5, 2, 6], [0, 0, 1, 2, 0, 0, 2, 1],
             [0, 1, 2, 11, 4, 5, 6, 10, 8, 9, 3, 7], [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1]),
}

# expand to all 18 face moves: X (90 CW), X2 (180), X' (90 CCW)
MOVES: dict[str, CubieCube] = {}
for face in ["U", "R", "F", "D", "L", "B"]:
    base = MOVE_CUBES[face]
    cur = CubieCube()
    for power, suffix in [(1, ""), (2, "2"), (3, "'")]:
        cur = cur.copy()
        cur.multiply(base)
        MOVES[face + suffix] = cur.copy()


def apply_sequence(seq) -> CubieCube:
    """Build the cube resulting from applying a move sequence to a solved cube."""
    c = CubieCube()
    for mv in (seq.split() if isinstance(seq, str) else seq):
        c.multiply(MOVES[mv])
    return c


if __name__ == "__main__":
    # ---- self tests ----
    def expect(name, cond):
        print(f"[{'OK ' if cond else 'FAIL'}] {name}")
        assert cond, name

    # R^4 = identity
    expect("R^4 = I", apply_sequence("R R R R").is_solved())
    # every face^4 = identity
    for f in ["U", "R", "F", "D", "L", "B"]:
        expect(f"{f}^4 = I", apply_sequence([f, f, f, f]).is_solved())
    # X X' = identity
    for f in ["U", "R", "F", "D", "L", "B"]:
        expect(f"{f} {f}' = I", apply_sequence([f, f + "'"]).is_solved())
    # X2 = X X
    for f in ["U", "R", "F", "D", "L", "B"]:
        a = apply_sequence([f + "2"])
        b = apply_sequence([f, f])
        expect(f"{f}2 = {f} {f}", a == b)
    # sexy move (R U R' U') ^ 6 = identity
    expect("(R U R' U')^6 = I", apply_sequence("R U R' U' " * 6).is_solved())
    # superflip is NOT solved but returns home corners (sanity: not solved)
    superflip = "U R2 F B R B2 R U2 L B2 R U' D' R2 F R' L B2 U2 F2"
    sf = apply_sequence(superflip)
    expect("superflip cp = identity (all edges flipped)", sf.cp == list(range(8)))
    expect("superflip not solved", not sf.is_solved())
    print("\nall cubie-level self tests passed.")
