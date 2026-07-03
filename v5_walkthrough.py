"""V5 (子群链) 全流程演示: EO凑 -> DR凑 -> HTR段 -> 半转先角 -> 半转收棱.
每段给出引擎核算的状态信息, 供人类思路解说.
"""
import sys, time
from collections import deque
from cubie import CubieCube, MOVES, apply_sequence
import coord as C
from tables import load, MOVE_NAMES

EDGE_NAMES = ["UR","UF","UL","UB","DR","DF","DL","DB","FR","FL","BL","BR"]
CORNER_NAMES = ["URF","UFL","ULB","UBR","DFR","DLF","DBL","DRB"]
HALF = ["U2","D2","R2","L2","F2","B2"]
G1M = ["U","U2","U'","D","D2","D'","R2","L2","F2","B2"]
EO_SAFE_N = [m for m in MOVE_NAMES if not (m[0] in "FB" and m[1:] in ("","'"))]

T = load()
tm, fm, sm = T["twist_move"], T["flip_move"], T["slice_move"]
pts = T["prun_twist_slice"]
NS = C.N_SLICE

def bad_edges(c):
    return [EDGE_NAMES[i] for i in range(12) if c.eo[i] == 1]
def bad_corners(c):
    return [CORNER_NAMES[i] for i in range(8) if c.co[i] != 0]
def slice_home(c):
    return sum(1 for i in range(8, 12) if c.ep[i] >= 8)

# ---------- EO optimal ----------
PF = bytearray([255]) * C.N_FLIP; PF[0] = 0
fr, d = [0], 0
while fr:
    nx = []
    for f in fr:
        for m in range(18):
            g = fm[f][m]
            if PF[g] == 255: PF[g] = d + 1; nx.append(g)
    fr = nx; d += 1

def solve_eo(cube):
    sol = []
    def search(f, depth, bound, last):
        if depth + PF[f] > bound: return False
        if f == 0: return True
        for mi in range(18):
            if last >= 0 and mi // 3 == last // 3: continue
            sol.append(mi)
            if search(fm[f][mi], depth + 1, bound, mi): return True
            sol.pop()
        return False
    b = PF[C.get_flip(cube)]
    while True:
        sol.clear()
        if search(C.get_flip(cube), 0, b, -1): return [MOVE_NAMES[i] for i in sol]
        b += 1

# ---------- DR part optimal (EO-safe moves) ----------
def solve_dr(cube):
    idxs = [MOVE_NAMES.index(m) for m in EO_SAFE_N]
    sol = []
    def search(tw, sl, depth, bound, last):
        if depth + pts[tw * NS + sl] > bound: return False
        if tw == 0 and sl == C.SLICE_SOLVED: return True
        for mi in idxs:
            if last >= 0 and mi // 3 == last // 3: continue
            sol.append(mi)
            if search(tm[tw][mi], sm[sl][mi], depth + 1, bound, mi): return True
            sol.pop()
        return False
    tw, sl = C.get_twist(cube), C.get_slice(cube)
    b = pts[tw * NS + sl]
    while True:
        sol.clear()
        if search(tw, sl, 0, b, -1): return [MOVE_NAMES[i] for i in sol]
        b += 1

# ---------- G3 machinery ----------
def pack(c):
    v = 0
    for x in c.cp: v = v * 8 + x
    for x in c.ep: v = v * 12 + x
    return v

print("building G3...", flush=True)
t0 = time.time()
solved = CubieCube()
G3D = {pack(solved): 0}
q = deque([solved]); G3CUBES = [solved]
while q:
    c = q.popleft(); dd = G3D[pack(c)]
    for m in HALF:
        c2 = c.copy(); c2.multiply(MOVES[m])
        k = pack(c2)
        if k not in G3D:
            G3D[k] = dd + 1; q.append(c2); G3CUBES.append(c2)
G3SET = set(G3D)
import pickle
with open("htr_coset.pkl", "rb") as f:
    _H = pickle.load(f)
CPS, EPS = _H["CPS"], _H["EPS"]
CID, EID = _H["cid"], _H["eid"]
CTRANS, ETRANS = _H["ctrans"], _H["etrans"]
HDIST = _H["dist"]

def coset_ids(c):
    kc = min(tuple(g[c.cp[i]] for i in range(8)) for g in CPS)
    ke = min(tuple(g[c.ep[i]] for i in range(12)) for g in EPS)
    return CID[kc], EID[ke]
# corner distance within G3 (96)
cd = {tuple(solved.cp): 0}
q = deque([solved])
while q:
    c = q.popleft()
    for m in HALF:
        c2 = c.copy(); c2.multiply(MOVES[m])
        k = tuple(c2.cp)
        if k not in cd: cd[k] = cd[tuple(c.cp)] + 1; q.append(c2)
print(f"  G3 {len(G3SET)}, corners {len(cd)} ({time.time()-t0:.0f}s)", flush=True)

def solve_htr(cube):
    """optimal G1-move sequence into G3 via exact coset-distance descent."""
    a, b = coset_ids(cube)
    path = []
    while HDIST[(a, b)] > 0:
        d = HDIST[(a, b)]
        for mi, m in enumerate(G1M):
            k = (CTRANS[a][mi], ETRANS[b][mi])
            if HDIST[k] == d - 1:
                path.append(m)
                a, b = k
                break
    return path

def greedy_corners(cube):
    seq = []
    c = cube.copy()
    while c.cp != list(range(8)):
        best = None
        for m in HALF:
            c2 = c.copy(); c2.multiply(MOVES[m])
            dd = cd[tuple(c2.cp)]
            if best is None or dd < best[0]:
                best = (dd, m, c2)
        seq.append(best[1]); c = best[2]
    return seq, c

def greedy_finish(cube):
    seq = []
    c = cube.copy()
    while not c.is_solved():
        best = None
        for m in HALF:
            c2 = c.copy(); c2.multiply(MOVES[m])
            dd = G3D[pack(c2)]
            if best is None or dd < best[0]:
                best = (dd, m, c2)
        seq.append(best[1]); c = best[2]
    return seq, c

def show(c):
    return (f"坏棱{len(bad_edges(c))}: {','.join(bad_edges(c)) or '-'} | "
            f"坏角{len(bad_corners(c))}: {','.join(bad_corners(c)) or '-'} | "
            f"中层归位 {slice_home(c)}/4")

def main():
    scr = sys.argv[1] if len(sys.argv) > 1 else \
        "R' D U L' B' F L D' R U' R B' U' B' U D' L' R F' B' L' F' U L U'"
    print(f"\n打乱: {scr}")
    cube = apply_sequence(scr)
    print(f"起始: {show(cube)}\n")

    # EO
    eo = solve_eo(cube)
    print(f"[台阶1 EO] {' '.join(eo)}  ({len(eo)}步)")
    for m in eo:
        cube.multiply(MOVES[m])
        print(f"   {m:3s} -> 坏棱: {','.join(bad_edges(cube)) or '全好 ✓'}")
    assert C.get_flip(cube) == 0

    # DR
    dr = solve_dr(cube)
    print(f"\n[台阶2 CO+中层] {' '.join(dr)}  ({len(dr)}步)")
    for m in dr:
        cube.multiply(MOVES[m])
        print(f"   {m:3s} -> 坏角: {','.join(bad_corners(cube)) or '全好 ✓':30s} 中层 {slice_home(cube)}/4")
    assert C.get_twist(cube) == 0 and C.get_slice(cube) == C.SLICE_SOLVED
    assert C.get_flip(cube) == 0
    print("   ★ 里程碑1 (DR) 达成: 全定向+中层归层. 此后只用 U D R2 L2 F2 B2.")

    # HTR
    print("\n[跳2 HTR]")
    htr = solve_htr(cube)
    assert htr is not None
    for m in htr:
        cube.multiply(MOVES[m])
    print(f"   {' '.join(htr)}  ({len(htr)}步)")
    assert pack(cube) in G3SET
    print("   ★ 里程碑2 (HTR) 达成: 六面两色化, 此后只用 180° 转.")

    # finish: corners then edges
    print("\n[收尾-先角]")
    cseq, cube = greedy_corners(cube)
    print(f"   {' '.join(cseq) or '(角已对)'}  ({len(cseq)}步)")
    print("\n[收尾-收棱]")
    eseq, cube = greedy_finish(cube)
    print(f"   {' '.join(eseq)}  ({len(eseq)}步)")
    assert cube.is_solved()

    total = eo + dr + htr + cseq + eseq
    v = apply_sequence(scr)
    for m in total: v.multiply(MOVES[m])
    assert v.is_solved()
    print(f"\n完全还原 ✓  总步数 {len(total)}: EO{len(eo)} + DR{len(dr)} + HTR{len(htr)} "
          f"+ 角{len(cseq)} + 棱{len(eseq)}")
    print(f"整串: {' '.join(total)}")

if __name__ == "__main__":
    main()
