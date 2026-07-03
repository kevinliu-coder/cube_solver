"""里程碑链 v3: 全查表流水线, 凑=0.

角(13, 人肉) -> [EO表] 全棱定向 -> [中层表] 中层归层 -> [分层表] 顶底分层
             -> [终表940] 还原

每张表的索引都只依赖"图案"(翻色位置/中层棱位置/顶层棱位置), 与其余
排列无关, 因此查表无需知道整体状态. 每条公式净不动角和中心.

  EO表:   2048 个翻色图案 -> <y,z2> 折叠, 公式用全部18种面转
  中层表: 495 个中层棱位置集 -> 折叠, 公式用EO安全转动(U D R L F2 B2)
  分层表: 70 个顶棱位置集 -> 折叠, 公式用G1转动(U D R2 L2 F2 B2)
"""
import itertools, time, random
import numpy as np
from math import comb
from cubie import CubieCube, MOVES, apply_sequence
import coord as C
from tables import MOVE_NAMES
import rotsym
import array as _arr

NT = C.N_TWIST
PCF = bytes(np.load("prun_corner_full.npy"))

def _load_bin(path, n):
    a = _arr.array("H")
    with open(path, "rb") as f:
        a.fromfile(f, n * 18)
    return [a[i * 18:(i + 1) * 18] for i in range(n)]
CPM = _load_bin("cpm.bin", C.N_CPERM)
TWM = _load_bin("twm.bin", C.N_TWIST)

FLIP_MOVE = None
def _flip_move():
    global FLIP_MOVE
    if FLIP_MOVE is None:
        FLIP_MOVE = [[0]*18 for _ in range(C.N_FLIP)]
        for f in range(C.N_FLIP):
            base = CubieCube(); C.set_flip(base, f)
            for mi, mn in enumerate(MOVE_NAMES):
                cc = base.copy(); cc.edge_multiply(MOVES[mn])
                FLIP_MOVE[f][mi] = C.get_flip(cc)
    return FLIP_MOVE

# ---------- strong table for EO stage: (flip x cperm) ----------
def flip_cp_table():
    import os
    if os.path.exists("prun_flip_cp.npy"):
        return bytes(np.load("prun_flip_cp.npy"))
    fm = np.array(_flip_move(), dtype=np.int32)
    cpm = np.array([list(r) for r in CPM], dtype=np.int32)
    n_a, n_b = C.N_FLIP, C.N_CPERM
    dist = np.full(n_a * n_b, 255, dtype=np.uint8)
    dist[0] = 0
    d = 0
    while True:
        fr = np.nonzero(dist == d)[0]
        if fr.size == 0:
            break
        a, b = fr // n_b, fr % n_b
        for m in range(18):
            ni = fm[a, m].astype(np.int64) * n_b + cpm[b, m]
            mask = dist[ni] == 255
            dist[ni[mask]] = d + 1
        print(f"  flip-cp depth {d}: {fr.size}", flush=True)
        d += 1
    np.save("prun_flip_cp.npy", dist)
    return bytes(dist)

# ---------- generic IDA* over coordinate tuple ----------
def ida(start, moves_idx, step, goal, h, max_depth=18):
    sol = []
    def search(st, depth, bound, last):
        lb = h(st)
        if depth + lb > bound:
            return False
        if lb == 0 and goal(st):
            return True
        if depth == bound:
            return False
        for mi in moves_idx:
            if last >= 0 and mi // 3 == last // 3:
                continue
            sol.append(mi)
            if search(step(st, mi), depth + 1, bound, mi):
                return True
            sol.pop()
        return False
    for bound in range(h(start), max_depth + 1):
        sol.clear()
        if search(start, 0, bound, -1):
            return [MOVE_NAMES[i] for i in sol]
    return None

# ---------- symmetry folding on patterns ----------
SYMS = rotsym.build_syms()

def fold(states, key_fn):
    """states: dict key->CubieCube. returns reps dict key->(alg placeholder)"""
    canon = {}
    reps = []
    for k, cc in states.items():
        if k in canon:
            continue
        orbit = {}
        for si, (g, fmap) in enumerate(SYMS):
            c2 = rotsym.conj(cc, g)
            k2 = key_fn(c2)
            if k2 not in orbit:
                orbit[k2] = si
        rep = min(orbit)
        for k2, si in orbit.items():
            canon[k2] = (rep, si)
        reps.append(rep)
    reps = sorted(set(r for r, _ in canon.values()))
    return reps, canon

def verify_random(state_maker, alg, checker, n=20):
    for _ in range(n):
        c = state_maker()
        for m in alg:
            c.multiply(MOVES[m])
        assert checker(c), alg

def main():
    t0 = time.time()
    random.seed(1)

    # ============ EO bank ============
    print("EO bank: building flip-cp table...", flush=True)
    PFC = flip_cp_table()
    fm = _flip_move()

    states = {}
    for f in range(C.N_FLIP):
        c = CubieCube(); C.set_flip(c, f)
        states[f] = c
    reps, canon = fold(states, C.get_flip)
    print(f"EO patterns: 2048 -> {len(reps)} classes", flush=True)

    def eo_h(st):
        f, cp, tw = st
        a = PFC[f * C.N_CPERM + cp]
        b = PCF[cp * NT + tw]
        return a if a > b else b

    eo_bank = {}
    for n, f in enumerate(reps):
        alg = ida((f, 0, 0), range(18),
                  lambda st, mi: (fm[st[0]][mi], CPM[st[1]][mi], TWM[st[2]][mi]),
                  lambda st: st == (0, 0, 0), eo_h)
        assert alg is not None
        # verify on random underlying permutations
        def mk(f=f):
            c = CubieCube(); C.set_flip(c, f)
            perm = list(range(12)); random.shuffle(perm)
            # keep permutation parity even (corners solved)
            inv = sum(1 for i in range(12) for j in range(i+1,12) if perm[i]>perm[j])
            if inv % 2: perm[0], perm[1] = perm[1], perm[0]
            eo = c.eo[:]
            c.ep = perm
            c.eo = [eo[i] for i in range(12)]
            return c
        verify_random(mk, alg,
                      lambda c: C.get_flip(c) == 0 and c.cp == list(range(8))
                                and c.co == [0] * 8, n=5)
        eo_bank[f] = alg
        if (n + 1) % 50 == 0:
            print(f"  {n+1}/{len(reps)} ({time.time()-t0:.0f}s)", flush=True)
    lens = [len(a) for a in eo_bank.values()]
    print(f"EO bank: {len(eo_bank)} formulas, avg {sum(lens)/len(lens):.1f}, "
          f"max {max(lens)}  ({time.time()-t0:.0f}s)\n", flush=True)

    # ============ middle-layer bank ============
    # index: which 4 slots hold the slice cubies (slice coordinate 0..494)
    EO_SAFE = [i for i, m in enumerate(MOVE_NAMES)
               if not (m[0] in "FB" and m[1:] in ("", "'"))]  # 14 moves
    sm = [[0]*18 for _ in range(C.N_SLICE)]
    for s in range(C.N_SLICE):
        base = CubieCube(); C.set_slice(base, s)
        for mi, mn in enumerate(MOVE_NAMES):
            cc = base.copy(); cc.edge_multiply(MOVES[mn])
            sm[s][mi] = C.get_slice(cc)
    # small exact table (slice x cperm) under EO-safe moves
    smn = np.array(sm, dtype=np.int32)
    cpn = np.array([list(r) for r in CPM], dtype=np.int32)
    dist = np.full(C.N_SLICE * C.N_CPERM, 255, dtype=np.uint8)
    dist[C.SLICE_SOLVED * C.N_CPERM + 0] = 0
    d = 0
    while True:
        fr = np.nonzero(dist == d)[0]
        if fr.size == 0:
            break
        a, b = fr // C.N_CPERM, fr % C.N_CPERM
        for m in EO_SAFE:
            ni = smn[a, m].astype(np.int64) * C.N_CPERM + cpn[b, m]
            mask = dist[ni] == 255
            dist[ni[mask]] = d + 1
        d += 1
    PSC = bytes(dist)

    states = {}
    for s in range(C.N_SLICE):
        c = CubieCube(); C.set_slice(c, s)
        states[s] = c
    reps, canon = fold(states, C.get_slice)
    print(f"middle patterns: 495 -> {len(reps)} classes", flush=True)

    def mid_h(st):
        s, cp, tw = st
        a = PSC[s * C.N_CPERM + cp]
        b = PCF[cp * NT + tw]
        return a if a > b else b

    mid_bank = {}
    for s in reps:
        alg = ida((s, 0, 0), EO_SAFE,
                  lambda st, mi: (sm[st[0]][mi], CPM[st[1]][mi], TWM[st[2]][mi]),
                  lambda st: st[0] == C.SLICE_SOLVED and st[1] == 0 and st[2] == 0,
                  mid_h)
        assert alg is not None
        mid_bank[s] = alg
    lens = [len(a) for a in mid_bank.values()]
    print(f"middle bank: {len(mid_bank)} formulas, avg {sum(lens)/len(lens):.1f}, "
          f"max {max(lens)}  ({time.time()-t0:.0f}s)\n", flush=True)

    # ============ separation bank ============
    # index: which 4 of the 8 UD slots hold U-cubies. G1 moves only.
    G1 = [MOVE_NAMES.index(m) for m in
          ["U", "U2", "U'", "D", "D2", "D'", "R2", "L2", "F2", "B2"]]
    def sep_key(c):
        return tuple(sorted(i for i in range(8) if c.ep[i] < 4))
    states = {}
    for pos in itertools.combinations(range(8), 4):
        c = CubieCube()
        us, ds = list(pos), [i for i in range(8) if i not in pos]
        ep = [0]*12
        for i, p in enumerate(us): ep[p] = i
        for i, p in enumerate(ds): ep[p] = 4 + i
        ep[8:] = [8, 9, 10, 11]
        c.ep = ep
        states[tuple(pos)] = c
    reps, canon = fold(states, sep_key)
    print(f"separation patterns: 70 -> {len(reps)} classes", flush=True)

    sep_bank = {}
    for pos in reps:
        c0 = states[pos]
        def step(st, mi):
            c = st.copy(); c.multiply(MOVES[MOVE_NAMES[mi]]); return c
        def goal(c):
            return (all(c.ep[i] < 4 for i in range(4)) and c.cp == list(range(8)))
        def h(c):
            cp, tw = C.get_corner_perm(c), C.get_twist(c)
            return PCF[cp * NT + tw]
        alg = ida(c0, G1, step, goal, h, max_depth=12)
        assert alg is not None
        sep_bank[pos] = alg
    lens = [len(a) for a in sep_bank.values()]
    print(f"separation bank: {len(sep_bank)} formulas, avg {sum(lens)/len(lens):.1f}, "
          f"max {max(lens)}  ({time.time()-t0:.0f}s)\n", flush=True)

    # ============ summary ============
    n_eo, n_mid, n_sep = len(eo_bank), len(mid_bank), len(sep_bank)
    a_eo = sum(len(a) for a in eo_bank.values()) / n_eo
    a_mid = sum(len(a) for a in mid_bank.values()) / n_mid
    a_sep = sum(len(a) for a in sep_bank.values()) / n_sep
    print("=" * 60)
    print(f"里程碑链公式量: EO {n_eo} + 中层 {n_mid} + 分层 {n_sep} + 终表 940 "
          f"= {n_eo + n_mid + n_sep + 940}")
    print(f"平均步数: 角13 + EO {a_eo:.1f} + 中层 {a_mid:.1f} + 分层 {a_sep:.1f} "
          f"+ 终表 12.6 = {13 + a_eo + a_mid + a_sep + 12.6:.1f}")

    with open("milestone_banks.txt", "w") as f:
        f.write("里程碑链公式库 (凑=0 全查表)\n" + "=" * 60 + "\n\n")
        f.write(f"--- EO表 ({n_eo}条, 按翻色图案索引) ---\n")
        for k in sorted(eo_bank, key=lambda k: len(eo_bank[k])):
            c = CubieCube(); C.set_flip(c, k)
            pat = " ".join(rotsym.map_move(n, {x: x for x in "URFDLB"}) or n
                           for n in [])
            names = [["UR","UF","UL","UB","DR","DF","DL","DB","FR","FL","BL","BR"][i]
                     for i in range(12) if c.eo[i]]
            f.write(f"翻:{','.join(names) or '-':40s} [{len(eo_bank[k]):2d}] "
                    f"{' '.join(eo_bank[k])}\n")
        f.write(f"\n--- 中层表 ({n_mid}条, 按中层棱位置索引) ---\n")
        for k in sorted(mid_bank, key=lambda k: len(mid_bank[k])):
            c = CubieCube(); C.set_slice(c, k)
            pos = [["UR","UF","UL","UB","DR","DF","DL","DB","FR","FL","BL","BR"][i]
                   for i in range(12) if c.ep[i] >= 8]
            f.write(f"中层棱在:{','.join(pos):28s} [{len(mid_bank[k]):2d}] "
                    f"{' '.join(mid_bank[k])}\n")
        f.write(f"\n--- 分层表 ({n_sep}条, 按顶棱位置索引) ---\n")
        for k in sorted(sep_bank, key=lambda k: len(sep_bank[k])):
            pos = [["UR","UF","UL","UB","DR","DF","DL","DB"][i] for i in k]
            f.write(f"顶棱在:{','.join(pos):28s} [{len(sep_bank[k]):2d}] "
                    f"{' '.join(sep_bank[k])}\n")
    print("wrote milestone_banks.txt")

if __name__ == "__main__":
    main()
