"""One-look finish table for the corners-first method.

Precondition (reached by the 凑 phase):
  - all 8 corners solved
  - all 12 edges oriented (EO = 0)
  - every edge back in its home layer (U edges in U, D in D, E-slice in E)

Remaining states: 4! x 4! x 4! / 2 (even total parity) = 6912.
Each is solved by one formula using only {U, D, R2, L2, F2, B2} (phase 2),
which never breaks edge orientation and never twists corners mid-formula.

The 6912 states fold into equivalence classes under the 8 viewing angles
<y, z2>; only class representatives get an IDA* solve, the other angles'
formulas are derived by letter relabeling. Every one of the 6912 formulas
is verified against the cubie engine.

Outputs:
  onelook_canonical.txt  - the ~880 formulas a human learns
  onelook_full.csv       - all 6912 states -> formula (machine table)
"""
import itertools, time, sys
from collections import Counter
from cubie import CubieCube, MOVES
from tables import PHASE2_NAMES
from twophase import _solve_phase2
import rotsym

EDGE_NAMES = ["UR", "UF", "UL", "UB", "DR", "DF", "DL", "DB", "FR", "FL", "BL", "BR"]

PERMS4 = list(itertools.permutations(range(4)))

def perm_parity(p):
    inv = sum(1 for i in range(len(p)) for j in range(i + 1, len(p)) if p[i] > p[j])
    return inv & 1

def make_state(u, d, e):
    """State with U-layer edges permuted by u, D-layer by d, E-slice by e."""
    c = CubieCube()
    c.ep = [u[0], u[1], u[2], u[3],
            4 + d[0], 4 + d[1], 4 + d[2], 4 + d[3],
            8 + e[0], 8 + e[1], 8 + e[2], 8 + e[3]]
    return c

def state_key(c):
    return tuple(c.ep)

def in_set(c):
    """Sanity: state belongs to the precondition set."""
    return (c.cp == list(range(8)) and c.co == [0] * 8 and c.eo == [0] * 12
            and all(c.ep[i] < 4 for i in range(4))
            and all(4 <= c.ep[i] < 8 for i in range(4, 8))
            and all(c.ep[i] >= 8 for i in range(8, 12)))

def cycles_str(ep, base):
    """Human description of one layer's 4-edge permutation."""
    seen, parts = set(), []
    for i in range(4):
        if i in seen or ep[base + i] == base + i:
            seen.add(i)
            continue
        cyc, j = [], i
        while j not in seen:
            seen.add(j)
            cyc.append(j)
            j = ep[base + j] - base
        if len(cyc) == 2:
            parts.append(f"{EDGE_NAMES[base+cyc[0]]}<->{EDGE_NAMES[base+cyc[1]]}")
        else:
            parts.append("->".join(EDGE_NAMES[base + k] for k in cyc)
                         + "->" + EDGE_NAMES[base + cyc[0]])
    return " ".join(parts) if parts else "OK"

def main():
    syms = rotsym.build_syms()

    # ---- enumerate the 6912 states ----
    states = {}
    for u in PERMS4:
        for d in PERMS4:
            pu, pd = perm_parity(u), perm_parity(d)
            for e in PERMS4:
                if (pu + pd + perm_parity(e)) & 1:
                    continue
                c = make_state(u, d, e)
                assert in_set(c)
                states[state_key(c)] = c
    assert len(states) == 6912, len(states)
    print(f"enumerated {len(states)} precondition states")

    # ---- fold into <y, z2> classes ----
    canon = {}      # state_key -> (rep_key, sym_index)
    reps = []       # rep keys in discovery order
    for key, c in states.items():
        if key in canon:
            continue
        orbit = []
        for si, (g, fmap) in enumerate(syms):
            cc = rotsym.conj(c, g)
            assert in_set(cc), "orbit left the precondition set"
            orbit.append((state_key(cc), si))
        rep = min(k for k, _ in orbit)
        # register every orbit member: which sym turns the REP into it
        for k, si in orbit:
            if k not in canon:
                # c conj by sym si gives k; rep = c conj by sym s0
                canon[k] = (rep, si)
        reps.append(rep) if rep == key or rep not in set(reps) else None
    reps = sorted({r for r, _ in canon.values()})
    print(f"folded into {len(reps)} viewing-angle classes "
          f"(6912 / 8 = {6912 // 8} + {len(reps) - 6912 // 8} symmetric extras)")

    # canon maps every key to (rep, sym) but sym recorded relative to the first
    # orbit visitor, not the rep. Rebuild cleanly: for each rep, walk its orbit.
    canon = {}
    for rep in reps:
        c = states[rep]
        for si, (g, fmap) in enumerate(syms):
            k = state_key(rotsym.conj(c, g))
            if k not in canon:
                canon[k] = (rep, si)
    assert len(canon) == 6912

    # ---- solve each representative with phase-2 IDA* ----
    print("solving representatives (phase-2 optimal, moves in U D R2 L2 F2 B2)...")
    t0 = time.time()
    rep_alg = {}
    deadline = time.time() + 3600
    for n, rep in enumerate(reps):
        c = states[rep]
        sol = _solve_phase2(c, 18, deadline)
        assert sol is not None, rep
        alg = [PHASE2_NAMES[i] for i in sol]
        v = c.copy()
        for m in alg:
            v.multiply(MOVES[m])
        assert v.is_solved(), rep
        rep_alg[rep] = alg
        if (n + 1) % 100 == 0:
            print(f"  {n+1}/{len(reps)}  ({time.time()-t0:.0f}s)")
    print(f"  all {len(reps)} solved in {time.time()-t0:.0f}s")

    # ---- derive + verify all 6912 ----
    full = {}
    for key, (rep, si) in canon.items():
        g, fmap = syms[si]
        alg = rotsym.map_alg(rep_alg[rep], fmap)
        v = states[key].copy()
        for m in alg:
            v.multiply(MOVES[m])
        assert v.is_solved(), (key, rep, si)
        full[key] = (alg, rep, si)
    print(f"derived + verified all {len(full)} formulas")

    # ---- stats ----
    lens = [len(a) for a, _, _ in full.values()]
    dist = Counter(lens)
    avg = sum(lens) / len(lens)
    print(f"formula length: avg {avg:.2f}, max {max(lens)}")
    for L in sorted(dist):
        print(f"  {L:2d}步: {dist[L]:4d}")

    # ---- emit canonical (human) table ----
    rep_ids = {rep: i + 1 for i, rep in enumerate(
        sorted(reps, key=lambda r: (len(rep_alg[r]), r)))}
    with open("onelook_canonical.txt", "w") as f:
        f.write("角先一看收 (corners-first one-look) 公式表 — 核心视角类\n")
        f.write("前置: 8角全对 + 12棱全定向 + 每棱回本层\n")
        f.write("识别: 每层各看4条棱的排列 (角是参照系, 无AUF)\n")
        f.write("其余7个视角 = 整体y转/上下翻后按同一条公式的字母映射执行\n")
        f.write(f"共 {len(reps)} 条核心公式, 平均 {avg:.1f} 步\n")
        f.write("=" * 78 + "\n\n")
        for rep in sorted(reps, key=lambda r: (len(rep_alg[r]), r)):
            ep = list(rep)
            alg = rep_alg[rep]
            f.write(f"C{rep_ids[rep]:03d} [{len(alg):2d}步] "
                    f"U层: {cycles_str(ep, 0):34s} D层: {cycles_str(ep, 4):34s} "
                    f"E层: {cycles_str(ep, 8):34s}\n")
            f.write(f"      公式: {' '.join(alg)}\n\n")

    # ---- emit full machine table ----
    with open("onelook_full.csv", "w") as f:
        f.write("ep_0..11,canonical_id,sym_index,length,formula\n")
        for key in sorted(full):
            alg, rep, si = full[key]
            f.write(f"{' '.join(map(str, key))},C{rep_ids[rep]:03d},{si},"
                    f"{len(alg)},{' '.join(alg)}\n")

    print(f"\nwrote onelook_canonical.txt ({len(reps)} formulas) "
          f"and onelook_full.csv (6912 rows)")

if __name__ == "__main__":
    main()
