"""角安全基元工具箱 for the 凑 phase.

After the corners are solved, every intermediate checkpoint must leave the
corners intact (and, on a real cube, the centers). A primitive qualifies iff
  - net corner action = identity (corners may move mid-sequence)
  - net slice-turn count = 0 mod 4 per axis (centers return home)

Slice moves M/E/S are constructed from whole-cube rotations via the exact
relations  x = R M' L',  y = U E' D',  z = F S B'  and each rotation is
verified by its move-conjugation table, so the definitions cannot be wrong.

The toolkit itself is found by meet-in-the-middle search over <M,U,D>
(minimal sequences), plus verified [face, slice] commutators for the E-slice.
"""
from collections import deque
from cubie import CubieCube, MOVES
from rotsym import Y_ROT, conj, _inv, _mul

EDGE_NAMES = ["UR", "UF", "UL", "UB", "DR", "DF", "DL", "DB", "FR", "FL", "BL", "BR"]

# ---------- whole-cube rotations x and z (same style as Y_ROT, verified) ----------
# x: rotate like R (F->U, U->B, B->D, D->F)
X_ROT = None
# z: rotate like F (U->R, R->D, D->L, L->U)
Z_ROT = None

def _build_rotations():
    global X_ROT, Z_ROT
    # derive x and z from y and the known composition x = y-frame change:
    # easier: construct by brute force over candidate orientation bits is messy;
    # instead build x from the relation with z2/y is circular. Construct directly:
    # corners URF UFL ULB UBR DFR DLF DBL DRB ; edges UR UF UL UB DR DF DL DB FR FL BL BR
    # x (like R): URF->UBR? cubie at (U,R,F) moves: F->U so it lands (B?,R,U)... slot map:
    # slot URF receives old DFR ; UBR<-URF ; DRB<-UBR ; DFR<-DRB (R column), and the
    # L column: UFL<-DLF ; ULB<-UFL ; DBL<-ULB ; DLF<-DBL
    x = CubieCube()
    x.cp = [4, 5, 1, 0, 7, 6, 2, 3]
    # corner twists: same as R move pattern on the R column, mirrored on L column
    x.co = [2, 1, 2, 1, 1, 2, 1, 2]
    # edges: UF<-DF? F->U: slot UF receives old FD? slot UF <- DF(5)? no: F face rises to U:
    # UF <- FR? Work by faces: after x, U face shows old F face. Edge slot UF lies on U,F.
    # old edge now at UF came from (F,D) = DF. UB <- UF? old U goes to B: edge at UB came
    # from (U,F)=UF. DB <- UB, DF <- DB. UR <- FR, FR <- DR, DR <- BR, BR <- UR.
    # UL <- FL, FL <- DL, DL <- BL, BL <- UL.
    x.ep = [8, 5, 9, 1, 11, 7, 10, 3, 4, 6, 2, 0]
    x.eo = [1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1]
    # z (like F, U->R) is x with its axis relabeled by y: try both conjugation
    # directions, verification below picks the correct one.
    cand1 = conj(x, Y_ROT)
    cand2 = conj(x, _inv(Y_ROT))
    z = None
    for cand in (cand1, cand2):
        try:
            _verify_rotation("z", cand, Z_FACE)
            z = cand
            break
        except AssertionError:
            continue
    assert z is not None, "could not derive z from x and y"
    X_ROT, Z_ROT = x, z

X_FACE = {"F": "U", "U": "B", "B": "D", "D": "F", "R": "R", "L": "L"}
Z_FACE = {"U": "R", "R": "D", "D": "L", "L": "U", "F": "F", "B": "B"}

def _verify_rotation(name, rot, fmap):
    r4 = CubieCube()
    for _ in range(4):
        r4 = _mul(r4, rot)
    assert r4.is_solved(), f"{name}^4 != I"
    for f in "URFDLB":
        for suf in ["", "2", "'"]:
            assert conj(MOVES[f + suf], rot) == MOVES[fmap[f] + suf], (name, f + suf)

_build_rotations()

# ---------- slice moves from exact relations ----------
def _build_slices():
    # x = R M' L'  =>  M' = R' x L   (apply-order composition = left-to-right multiply)
    mp = _mul(_mul(MOVES["R'"], X_ROT), MOVES["L"])
    m = _inv(mp)
    # y = U E' D'  =>  E' = U' y D
    ep_ = _mul(_mul(MOVES["U'"], Y_ROT), MOVES["D"])
    e = _inv(ep_)
    # z = F S B'  =>  S = F' z B
    s = _mul(_mul(MOVES["F'"], Z_ROT), MOVES["B"])
    out = {}
    for nm, base in [("M", m), ("E", e), ("S", s)]:
        cur = CubieCube()
        for power, suffix in [(1, ""), (2, "2"), (3, "'")]:
            cur = _mul(cur, base)
            out[nm + suffix] = cur.copy()
        r4 = _mul(cur, base)
        assert r4.is_solved(), f"{nm}^4 != I"
        assert base.cp == list(range(8)) and base.co == [0] * 8, f"{nm} touches corners"
    return out

def verify_all():
    _verify_rotation("x", X_ROT, X_FACE)
    _verify_rotation("z", Z_ROT, Z_FACE)
    S = _build_slices()
    # ground-truth cross-checks with famous MU algs:
    # Ua perm:  M2 U M U2 M' U M2  ==  R U' R U R U R U' R' U' R2
    a = CubieCube()
    for mv in "M2 U M U2 M' U M2".split():
        a.multiply(S[mv] if mv[0] in "MES" else MOVES[mv])
    b = CubieCube()
    for mv in "R U' R U R U R U' R' U' R2".split():
        b.multiply(MOVES[mv])
    assert a == b, "Ua cross-check failed: M orientation convention wrong"
    # H perm: M2 U M2 U2 M2 U M2 == pure (UF<->UB)(UR<->UL)... verify shape
    h = CubieCube()
    for mv in "M2 U M2 U2 M2 U M2".split():
        h.multiply(S[mv] if mv[0] in "MES" else MOVES[mv])
    want_ep = list(range(12)); want_ep[1], want_ep[3] = 3, 1; want_ep[0], want_ep[2] = 2, 0
    assert h.cp == list(range(8)) and h.eo == [0] * 12 and h.ep == want_ep, "H perm check"
    print("[OK ] x, z rotations; M, E, S slice moves; Ua & H cross-checks")
    return S

SLICES = verify_all() if __name__ != "__main__" else None

# ---------- meet-in-the-middle search over <M, U, D> ----------
GEN_MUD = ["M", "M'", "M2", "U", "U'", "U2", "D", "D'", "D2"]
M_NET = {"M": 1, "M'": 3, "M2": 2}

def _cube_of(mv, S):
    return S[mv] if mv[0] in "MES" else MOVES[mv]

def _key(c, mnet):
    return (tuple(c.ep), tuple(c.eo), tuple(c.cp), mnet)

def _bfs_layer(S, depth):
    """states reachable from identity in <= depth MUD moves -> shortest seq."""
    start = CubieCube()
    seen = {_key(start, 0): []}
    frontier = [(start, 0, [])]
    for _ in range(depth):
        nxt = []
        for c, mnet, seq in frontier:
            last = seq[-1][0] if seq else ""
            for mv in GEN_MUD:
                if mv[0] == last:
                    continue
                c2 = _mul(c, _cube_of(mv, S))
                m2 = (mnet + M_NET.get(mv, 0)) % 4
                k = _key(c2, m2)
                if k not in seen:
                    seen[k] = seq + [mv]
                    nxt.append((c2, m2, seq + [mv]))
        frontier = nxt
    return seen

def find_mud(target: CubieCube, fwd, S, back_depth=6):
    """shortest MUD sequence equal to target with mnet==0, via MITM."""
    best = None
    # backward BFS from target: target * B(rev) ... we search A,B with A*B = T
    # equivalently A = T * B^{-1}; enumerate B^{-1} directly as suffix words.
    start = (target.copy(), 0, [])
    seen_b = {_key(target, 0): []}
    frontier = [start]
    def check(c, mnet, suffix):
        nonlocal best
        k = _key(c, (-mnet) % 4)
        # we need A with A = c meaning A's mnet must equal -mnet mod4? A*B=T:
        # A = T * B^{-1} = c ; mnet(A) + mnet(B) = 0 mod 4
        if k in fwd:
            cand = fwd[k] + suffix
            if best is None or len(cand) < len(best):
                best = cand
    check(target, 0, [])
    for _ in range(back_depth):
        nxt = []
        for c, mnet, suffix in frontier:
            first = suffix[0][0] if suffix else ""
            for mv in GEN_MUD:
                if mv[0] == first:
                    continue
                # prepend inverse relationship: T * (mv ... )^{-1}
                c2 = _mul(c, _inv(_cube_of(mv, S)))
                m2 = (mnet + M_NET.get(mv, 0)) % 4
                k = _key(c2, m2)
                if k in seen_b and len(seen_b[k]) <= len(suffix) + 1:
                    continue
                seen_b[k] = [mv] + suffix
                nxt.append((c2, m2, [mv] + suffix))
                check(c2, m2, [mv] + suffix)
        frontier = nxt
    return best

def edge_target(perm_pairs=None, cycles=None, flips=()):
    """Build a pure-edge target cube. cycles: list of slot-index cycles (cubie
    at cyc[i] moves to slot cyc[i+1]); flips: slots whose eo toggles."""
    c = CubieCube()
    if cycles:
        for cyc in cycles:
            src = [c.ep[i] for i in cyc]
            for i, slot in enumerate(cyc):
                c.ep[cyc[(i + 1) % len(cyc)]] = src[i]
    for f in flips:
        c.eo[f] ^= 1
    return c

def describe(c: CubieCube) -> str:
    parts = []
    seen = set()
    for i in range(12):
        if i in seen or c.ep[i] == i:
            continue
        cyc, j = [], i
        while j not in seen:
            seen.add(j)
            cyc.append(j)
            j = c.ep.index(c.ep[j]) if False else None
        break
    # simpler: report moved edges and flips directly
    mv = [f"{EDGE_NAMES[c.ep[i]]}->{EDGE_NAMES[i]}" for i in range(12) if c.ep[i] != i]
    fl = [EDGE_NAMES[i] for i in range(12) if c.eo[i] == 1]
    out = []
    if mv:
        out.append("换位: " + ", ".join(mv))
    if fl:
        out.append("翻色: " + ", ".join(fl))
    return " | ".join(out) if out else "恒等"

def verify_primitive(seq, S, expect: CubieCube | None = None):
    c = CubieCube()
    mnet = {"M": 0, "E": 0, "S": 0}
    for mv in seq:
        c.multiply(_cube_of(mv, S))
        if mv[0] in "MES":
            mnet[mv[0]] = (mnet[mv[0]] + {"": 1, "2": 2, "'": 3}[mv[1:]]) % 4
    ok_corner = c.cp == list(range(8)) and c.co == [0] * 8
    ok_center = all(v == 0 for v in mnet.values())
    assert ok_corner, f"{seq}: corners broken"
    assert ok_center, f"{seq}: centers displaced {mnet}"
    if expect is not None:
        assert c == expect, f"{seq}: wrong effect"
    return c

if __name__ == "__main__":
    S = verify_all()
    print("\nbuilding <M,U,D> forward table (depth 7)...")
    fwd = _bfs_layer(S, 7)
    print(f"  {len(fwd)} states")

    # UR UF UL UB DR DF DL DB FR FL BL BR = 0..11
    targets = [
        ("双翻 UF+UB (顶层对面两棱原地翻色)", edge_target(flips=(1, 3))),
        ("双翻 UF+DF (上下各一棱原地翻色)", edge_target(flips=(1, 5))),
        ("四翻 中轴四棱 UF UB DF DB", edge_target(flips=(1, 3, 5, 7))),
        ("顶层三循环 UR->UB->UL (Ub方向)", edge_target(cycles=[(0, 3, 2)])),
        ("上下对调 UF<->DF, UB<->DB", edge_target(cycles=[(1, 5), (3, 7)])),
        ("上下交叉 UF<->DB, UB<->DF", edge_target(cycles=[(1, 7), (3, 5)])),
        ("跨层三循环 UF->DF->DB->UF", edge_target(cycles=[(1, 5, 7)])),
        ("跨层三循环+翻 UF->DF(翻)->DB", None),  # placeholder skipped below
    ]
    print("\n=== <M,U,D> 角安全基元 (角/中心全程净不动) ===\n")
    for name, tgt in targets:
        if tgt is None:
            continue
        seq = find_mud(tgt, fwd, S, back_depth=6)
        if seq is None:
            print(f"{name}: 11步内未找到")
            continue
        got = verify_primitive(seq, S, tgt)
        print(f"{name}")
        print(f"  {' '.join(seq)}   ({len(seq)}步)")
        print(f"  效果: {describe(got)}\n")

    print("=== 中层(E层)基元: [面,切片]交换子, 角/中心净不动 ===\n")
    commutators = [
        "R E R' E'", "R' E R E'", "R E' R' E", "R2 E R2 E'",
        "F E F' E'", "F' E' F E", "F2 E2 F2 E2", "R E2 R' E2",
        "U S U' S'", "U' S' U S",
    ]
    for cs in commutators:
        seq = cs.split()
        got = verify_primitive(seq, S)
        print(f"  {cs:18s} -> {describe(got)}")
