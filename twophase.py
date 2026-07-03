"""Two-phase (Kociemba-style) solver.

Phase 1: reduce to G1 = <U,D,L2,R2,F2,B2>  (twist=flip=0, slice solved).
Phase 2: solve within G1 using only those 10 moves.

The outer loop deepens phase 1; every phase-1 solution is completed by an
optimal phase-2 solve, and the best total is kept. This is suboptimal in
general but typically lands within a couple moves of God's number.
"""
from __future__ import annotations
import time
from cubie import CubieCube, MOVES, apply_sequence
import coord as C
from tables import load, MOVE_NAMES, PHASE2_NAMES, PHASE2_IDX

_T = None  # tables, lazily loaded

def _tables():
    global _T
    if _T is None:
        _T = load()
    return _T

# face = move_idx // 3 ; axis groups U/D, R/L, F/B
def _opposite(face: int) -> int:
    return (face + 3) % 6

def _allowed(face: int, last1: int, last2: int) -> bool:
    if last1 == -1:
        return True
    if face == last1:
        return False
    if last2 != -1 and face == last2 and _opposite(face) == last1:
        return False
    return True


# ---------------- Phase 1 ----------------
def _phase1_solutions(twist, flip, slc, max_len, deadline):
    """Yield phase-1 move-index sequences (lists) of length <= max_len."""
    T = _tables()
    tm, fm, sm = T["twist_move"], T["flip_move"], T["slice_move"]
    pts, pfs = T["prun_twist_slice"], T["prun_flip_slice"]
    NS = C.N_SLICE
    sol = []

    def h(tw, fl, sl):
        return max(pts[tw * NS + sl], pfs[fl * NS + sl])

    def search(tw, fl, sl, depth, bound, last1, last2):
        if time.time() > deadline:
            return
        lb = h(tw, fl, sl)
        if depth + lb > bound:
            return
        if tw == 0 and fl == 0 and sl == C.SLICE_SOLVED:
            if depth == bound:
                yield list(sol)
            return
        for m in range(18):
            face = m // 3
            if not _allowed(face, last1, last2):
                continue
            sol.append(m)
            yield from search(tm[tw][m], fm[fl][m], sm[sl][m],
                              depth + 1, bound, face, last1)
            sol.pop()

    for bound in range(h(twist, flip, slc), max_len + 1):
        if time.time() > deadline:
            return
        yield from search(twist, flip, slc, 0, bound, -1, -1)


# ---------------- Phase 2 ----------------
def _solve_phase2(cube: CubieCube, max_len, deadline):
    """Optimal-within-bound phase-2 solve; returns list of MOVE_NAMES indices or None."""
    T = _tables()
    cm, em, smv = T["cperm_move"], T["eperm_move"], T["sperm_move"]
    pcs, pes = T["prun_cperm_sperm"], T["prun_eperm_sperm"]
    NSP = C.N_SPERM
    cp0 = C.get_corner_perm(cube)
    ep0 = C.get_edge8_perm(cube)
    sp0 = C.get_slice_perm(cube)
    sol = []

    def h(cp, ep, sp):
        return max(pcs[cp * NSP + sp], pes[ep * NSP + sp])

    def search(cp, ep, sp, depth, bound, last1, last2):
        if time.time() > deadline:
            return None
        lb = h(cp, ep, sp)
        if depth + lb > bound:
            return None
        if cp == 0 and ep == 0 and sp == 0:
            return list(sol) if depth == bound else None
        for mi in range(10):
            face = PHASE2_IDX[mi] // 3
            if not _allowed(face, last1, last2):
                continue
            sol.append(mi)
            r = search(cm[cp][mi], em[ep][mi], smv[sp][mi],
                       depth + 1, bound, face, last1)
            if r is not None:
                return r
            sol.pop()
        return None

    for bound in range(h(cp0, ep0, sp0), max_len + 1):
        sol.clear()
        r = search(cp0, ep0, sp0, 0, bound, -1, -1)
        if r is not None:
            return r
    return None


# ---------------- driver ----------------
def solve(scramble, max_total=30, timeout=10.0, verbose=False):
    """Return (solution_string, n_moves). scramble is a move string or list."""
    return solve_cube(apply_sequence(scramble), max_total, timeout, verbose)


def solve_cube(cube, max_total=30, timeout=10.0, verbose=False):
    """Solve a CubieCube directly. Return (solution_string, n_moves)."""
    if cube.is_solved():
        return "", 0
    deadline = time.time() + timeout
    twist, flip, slc = C.get_twist(cube), C.get_flip(cube), C.get_slice(cube)

    best = None
    best_len = max_total + 1
    for p1 in _phase1_solutions(twist, flip, slc, best_len - 1, deadline):
        if time.time() > deadline:
            break
        # apply phase-1 moves to reach a G1 cube
        g1 = cube.copy()
        for m in p1:
            g1.multiply(MOVES[MOVE_NAMES[m]])
        # phase 2 only worth it if it can beat current best
        p2_budget = best_len - len(p1) - 1
        if p2_budget < 0:
            # phase1 alone already too long -> no shorter total possible later
            break
        p2 = _solve_phase2(g1, p2_budget, deadline)
        if p2 is not None:
            total = [MOVE_NAMES[m] for m in p1] + [PHASE2_NAMES[i] for i in p2]
            if len(total) < best_len:
                best = total
                best_len = len(total)
                if verbose:
                    print(f"  found {best_len}: {' '.join(total)}")
    if best is None:
        return None, None
    return " ".join(best), best_len


def verify(scramble, solution) -> bool:
    cube = apply_sequence(scramble)
    for mv in solution.split():
        cube.multiply(MOVES[mv])
    return cube.is_solved()


if __name__ == "__main__":
    import random, sys
    load()  # ensure tables ready
    random.seed(42)
    print("solving 20 random scrambles (timeout 8s each)...\n")
    lengths = []
    t0 = time.time()
    for n in range(20):
        scr = " ".join(random.choice(MOVE_NAMES) for _ in range(25))
        sol, k = solve(scr, timeout=8.0)
        ok = verify(scr, sol) if sol is not None else False
        lengths.append(k)
        print(f"#{n:2d}  {k:2d} moves  {'OK' if ok else 'BAD'}   scramble: {scr}")
        assert ok, f"solution does not solve scramble #{n}"
    print(f"\navg {sum(lengths)/len(lengths):.1f} moves, "
          f"max {max(lengths)}, min {min(lengths)}  "
          f"({time.time()-t0:.1f}s total)")
