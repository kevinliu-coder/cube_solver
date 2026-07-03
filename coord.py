"""Coordinate level for the two-phase solver.

Phase 1 coordinates (reduce to subgroup G1 = <U,D,L2,R2,F2,B2>):
  twist  : corner orientation,  0..2186   (3^7)
  flip   : edge orientation,    0..2047   (2^11)
  slice  : UD-slice edge set,   0..494    (C(12,4)=495); solved value = 494
Phase 1 goal: twist=0, flip=0, slice=494.

Phase 2 coordinates (inside G1):
  corner_perm : permutation of 8 corners,        0..40319 (8!)
  edge8_perm  : permutation of 8 U/D-layer edges, 0..40319 (8!)
  slice_perm  : permutation of 4 slice edges,     0..23    (4!)
Phase 2 goal: all 0.
"""
from __future__ import annotations
from math import comb as C, factorial
from cubie import CubieCube

N_TWIST = 2187
N_FLIP = 2048
N_SLICE = 495
N_CPERM = 40320
N_EPERM = 40320
N_SPERM = 24

SLICE_EDGES = (8, 9, 10, 11)
SLICE_SOLVED = sum(C(SLICE_EDGES[i], i + 1) for i in range(4))  # = 494


# ---------- corner orientation (twist) ----------
def get_twist(cc: CubieCube) -> int:
    t = 0
    for i in range(7):
        t = 3 * t + cc.co[i]
    return t

def set_twist(cc: CubieCube, t: int) -> None:
    s = 0
    for i in range(6, -1, -1):
        cc.co[i] = t % 3
        s += cc.co[i]
        t //= 3
    cc.co[7] = (-s) % 3


# ---------- edge orientation (flip) ----------
def get_flip(cc: CubieCube) -> int:
    f = 0
    for i in range(11):
        f = 2 * f + cc.eo[i]
    return f

def set_flip(cc: CubieCube, f: int) -> None:
    s = 0
    for i in range(10, -1, -1):
        cc.eo[i] = f % 2
        s += cc.eo[i]
        f //= 2
    cc.eo[11] = (-s) % 2


# ---------- UD-slice edge set (positions, unordered) ----------
def get_slice(cc: CubieCube) -> int:
    positions = [j for j in range(12) if cc.ep[j] in SLICE_EDGES]
    return sum(C(positions[i], i + 1) for i in range(4))

def set_slice(cc: CubieCube, idx: int) -> None:
    # colexicographic unrank of a 4-subset of {0..11}
    positions = []
    rem = idx
    for i in range(3, -1, -1):
        p = i
        while C(p + 1, i + 1) <= rem:
            p += 1
        positions.append(p)
        rem -= C(p, i + 1)
    positions.sort()
    ep = [-1] * 12
    for si, p in enumerate(positions):
        ep[p] = SLICE_EDGES[si]
    others = [0, 1, 2, 3, 4, 5, 6, 7]
    oi = 0
    for j in range(12):
        if ep[j] == -1:
            ep[j] = others[oi]
            oi += 1
    cc.ep = ep


# ---------- generic permutation rank / unrank (factorial number system) ----------
def perm_rank(p: list[int]) -> int:
    n = len(p)
    r = 0
    for i in range(n):
        cnt = sum(1 for j in range(i + 1, n) if p[j] < p[i])
        r += cnt * factorial(n - 1 - i)
    return r

def perm_unrank(idx: int, n: int) -> list[int]:
    elems = list(range(n))
    perm = []
    for i in range(n):
        f = factorial(n - 1 - i)
        k = idx // f
        idx %= f
        perm.append(elems.pop(k))
    return perm


# ---------- phase-2 permutation coordinates ----------
def get_corner_perm(cc: CubieCube) -> int:
    return perm_rank(cc.cp)

def set_corner_perm(cc: CubieCube, idx: int) -> None:
    cc.cp = perm_unrank(idx, 8)

def get_edge8_perm(cc: CubieCube) -> int:
    return perm_rank(cc.ep[0:8])

def set_edge8_perm(cc: CubieCube, idx: int) -> None:
    cc.ep[0:8] = perm_unrank(idx, 8)

def get_slice_perm(cc: CubieCube) -> int:
    return perm_rank([v - 8 for v in cc.ep[8:12]])

def set_slice_perm(cc: CubieCube, idx: int) -> None:
    cc.ep[8:12] = [v + 8 for v in perm_unrank(idx, 4)]


if __name__ == "__main__":
    from cubie import MOVES, apply_sequence
    import random

    def expect(name, cond):
        print(f"[{'OK ' if cond else 'FAIL'}] {name}")
        assert cond, name

    solved = CubieCube()
    expect("solved twist = 0", get_twist(solved) == 0)
    expect("solved flip = 0", get_flip(solved) == 0)
    expect(f"solved slice = {SLICE_SOLVED}", get_slice(solved) == SLICE_SOLVED)
    expect("solved corner_perm = 0", get_corner_perm(solved) == 0)
    expect("solved edge8_perm = 0", get_edge8_perm(solved) == 0)
    expect("solved slice_perm = 0", get_slice_perm(solved) == 0)

    # round-trip get/set
    random.seed(1)
    for _ in range(2000):
        t = random.randrange(N_TWIST)
        c = CubieCube(); set_twist(c, t); assert get_twist(c) == t, ("twist", t)
        f = random.randrange(N_FLIP)
        c = CubieCube(); set_flip(c, f); assert get_flip(c) == f, ("flip", f)
        s = random.randrange(N_SLICE)
        c = CubieCube(); set_slice(c, s); assert get_slice(c) == s, ("slice", s, get_slice(c))
        cp = random.randrange(N_CPERM)
        c = CubieCube(); set_corner_perm(c, cp); assert get_corner_perm(c) == cp
        ep = random.randrange(N_EPERM)
        c = CubieCube(); set_edge8_perm(c, ep); assert get_edge8_perm(c) == ep
        sp = random.randrange(N_SPERM)
        c = CubieCube(); set_slice_perm(c, sp); assert get_slice_perm(c) == sp
    print("[OK ] all get/set round-trips (2000 each)")

    # coordinate transition consistency:
    # building a move table via (set coord -> apply move -> get coord) must agree
    # with applying the move to a fully-tracked cube.
    for _ in range(200):
        seq = [random.choice(list(MOVES)) for _ in range(8)]
        cube = apply_sequence(seq)
        mv = random.choice(list(MOVES))
        nxt = cube.copy(); nxt.multiply(MOVES[mv])
        # twist transition only needs co, flip only eo, slice only ep-set
        ta = CubieCube(); set_twist(ta, get_twist(cube)); ta.corner_multiply(MOVES[mv])
        assert get_twist(ta) == get_twist(nxt), "twist transition"
        fa = CubieCube(); set_flip(fa, get_flip(cube)); fa.edge_multiply(MOVES[mv])
        assert get_flip(fa) == get_flip(nxt), "flip transition"
        sa = CubieCube(); set_slice(sa, get_slice(cube)); sa.edge_multiply(MOVES[mv])
        assert get_slice(sa) == get_slice(nxt), "slice transition"
    print("[OK ] coordinate transitions match real moves (200 scrambles)")
    print("\nall coordinate self tests passed.")
