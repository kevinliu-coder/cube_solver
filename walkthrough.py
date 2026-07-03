"""全流程人类思路演示: 角(二阶) -> 凑(子目标+净不动工具) -> 查表一看收.

每个"块"都是净不动工具(做完角和中心归位), 模拟器里每块结束都可核对.
用法: python3 walkthrough.py "R' L U' R' B ..."
"""
import sys, time
import numpy as np
from cubie import CubieCube, MOVES, apply_sequence
import coord as C
from tables import MOVE_NAMES, PHASE2_NAMES
from cou_tools import SLICES, describe, _mul, _inv
from build_cou_tables import NSEP, SEP_SOLVED, sep_rank
import array as _arr

EDGE_NAMES = ["UR", "UF", "UL", "UB", "DR", "DF", "DL", "DB", "FR", "FL", "BL", "BR"]

def cube_of(m):
    return SLICES[m] if m[0] in "MES" else MOVES[m]

def apply_seq(c, seq):
    for m in seq:
        c.multiply(cube_of(m))

# ---------------- stage 1: corners ----------------
PCF = bytes(np.load("prun_corner_full.npy"))
NT = C.N_TWIST

def _load_bin(path, n):
    a = _arr.array("H")
    with open(path, "rb") as f:
        a.fromfile(f, n * 18)
    return [a[i * 18:(i + 1) * 18] for i in range(n)]
CPM = _load_bin("cpm.bin", C.N_CPERM)
TWM = _load_bin("twm.bin", C.N_TWIST)

def solve_corners_cube(cube):
    cp, tw = C.get_corner_perm(cube), C.get_twist(cube)
    sol = []
    def search(cp, tw, g, bound, last):
        if g + PCF[cp * NT + tw] > bound: return False
        if cp == 0 and tw == 0: return True
        for mi in range(18):
            if last >= 0 and mi // 3 == last // 3: continue
            sol.append(mi)
            if search(CPM[cp][mi], TWM[tw][mi], g + 1, bound, mi):
                return True
            sol.pop()
        return False
    bound = PCF[cp * NT + tw]
    while True:
        sol.clear()
        if search(cp, tw, 0, bound, -1):
            return [MOVE_NAMES[i] for i in sol]
        bound += 1

# ---------------- chunk libraries ----------------
def build_B_chunks():
    """Debt-style chunks for the E slice: [X e X'] sandwiches (3 moves, owes
    an E-turn) and bare E turns (1 move). Debt must return to 0 by the end."""
    lib = []  # (seq, effect_cube, debt)
    NET = {"E": 1, "E2": 2, "E'": 3}
    for X in ["R", "R'", "R2", "L", "L'", "L2", "F", "F'", "F2", "B", "B'", "B2"]:
        Xi = X[0] if X.endswith("'") else (X + "'" if len(X) == 1 else X)
        for e in ["E", "E'", "E2"]:
            seq = [X, e, Xi]
            c = CubieCube(); apply_seq(c, seq)
            assert c.cp == list(range(8)) and c.co == [0] * 8
            lib.append((seq, c, NET[e]))
    for e in ["E", "E'", "E2"]:
        c = CubieCube(); apply_seq(c, [e])
        lib.append(([e], c, NET[e]))
    return lib

def dijkstra_B(cube, lib, goal, max_moves=14):
    """min-total-moves over debt chunks; goal must hold with debt == 0."""
    import heapq
    start = (tuple(cube.ep), tuple(cube.eo), 0)
    h = [(0, 0, cube.copy(), 0, [])]
    dist = {start: 0}
    cnt = 0
    while h:
        cost, _, c, debt, path = heapq.heappop(h)
        if goal(c) and debt == 0:
            return path
        if cost >= max_moves:
            continue
        for seq, eff, d in lib:
            c2 = c.copy(); c2.multiply(eff)
            nd = (debt + d) % 4
            k = (tuple(c2.ep), tuple(c2.eo), nd)
            nc = cost + len(seq)
            if dist.get(k, 99) <= nc:
                continue
            dist[k] = nc
            cnt += 1
            heapq.heappush(h, (nc, cnt, c2, nd, path + [(seq, c2.copy(), nd)]))
    return None

def build_AC_chunks():
    """net-zero tools over <U,D,M,S> up to 5 moves (they never touch E slots),
    plus the two 12-move double-flips per axis."""
    from collections import deque
    GENS = [f + s for f in ["U", "D"] for s in ["", "2", "'"]] + \
           [f + s for f in ["M", "S"] for s in ["", "2", "'"]]
    NET = {"": 1, "2": 2, "'": 3}
    best = {}
    q = deque([(CubieCube(), {"M": 0, "S": 0}, [])])
    seen = set()
    while q:
        c, net, seq = q.popleft()
        if len(seq) >= 5:
            continue
        for m in GENS:
            if seq and m[0] == seq[-1][0]:
                continue
            c2 = c.copy(); c2.multiply(cube_of(m))
            n2 = dict(net)
            if m[0] in "MS":
                n2[m[0]] = (n2[m[0]] + NET[m[1:]]) % 4
            k = (tuple(c2.ep), tuple(c2.eo), tuple(c2.cp), n2["M"], n2["S"])
            if k in seen:
                continue
            seen.add(k)
            s2 = seq + [m]
            if (c2.cp == list(range(8)) and c2.co == [0] * 8
                    and n2["M"] == 0 and n2["S"] == 0 and not c2.is_solved()):
                ek = (tuple(c2.ep), tuple(c2.eo))
                if ek not in best or len(s2) < len(best[ek][0]):
                    best[ek] = (s2, c2.copy())
            q.append((c2, n2, s2))
    lib = list(best.values())
    # double flips, M axis and S axis
    for alg in ["U2 M' U M' U M' U2 M U M U M",
                "U M U M U2 M' U M' U M' U2 M"]:
        for repl in ["M", "S"]:
            seq = [m.replace("M", repl) for m in alg.split()]
            c = CubieCube(); apply_seq(c, seq)
            if c.cp == list(range(8)) and c.co == [0] * 8:
                lib.append((seq, c))
    return lib

# ---------------- searches ----------------
def slice_done(c):
    return all(c.ep[i] >= 8 and c.eo[i] == 0 for i in range(8, 12))

def ac_done(c):
    return (all(c.ep[i] < 4 for i in range(4))
            and all(4 <= c.ep[i] < 8 for i in range(4, 8))
            and c.eo[:8] == [0] * 8)

def bfs_chunks(cube, lib, goal, max_chunks=4):
    """BFS at chunk level; returns list of (seq, intent-cube-after)."""
    from collections import deque
    start = cube.copy()
    if goal(start):
        return []
    q = deque([(start, [])])
    seen = {(tuple(start.ep), tuple(start.eo))}
    while q:
        c, path = q.popleft()
        if len(path) >= max_chunks:
            continue
        for seq, eff in lib:
            c2 = c.copy()
            c2.multiply(eff)
            k = (tuple(c2.ep), tuple(c2.eo))
            if k in seen:
                continue
            seen.add(k)
            p2 = path + [(seq, c2.copy())]
            if goal(c2):
                return p2
            q.append((c2, p2))
    return None

def beam_chunks(cube, lib, goal, score, beam=800, depth=6):
    """beam search fallback for the A+C stage."""
    layer = [(score(cube), cube.copy(), [])]
    seen = {(tuple(cube.ep), tuple(cube.eo))}
    for _ in range(depth):
        nxt = []
        for _, c, path in layer:
            for seq, eff in lib:
                c2 = c.copy()
                c2.multiply(eff)
                k = (tuple(c2.ep), tuple(c2.eo))
                if k in seen:
                    continue
                seen.add(k)
                p2 = path + [(seq, c2.copy())]
                if goal(c2):
                    return p2
                nxt.append((score(c2), c2, p2))
        nxt.sort(key=lambda t: (t[0], sum(len(s) for s, _ in t[2])))
        layer = nxt[:beam]
        if not layer:
            break
    return None

# ---------------- state narration ----------------
def narrate_edges(c):
    mids_out = [(EDGE_NAMES[c.ep[i]], EDGE_NAMES[i]) for i in range(12)
                if c.ep[i] >= 8 and i < 8]
    flipped = [EDGE_NAMES[i] for i in range(12) if c.eo[i] == 1]
    wrong_layer = [EDGE_NAMES[c.ep[i]] for i in range(8)
                   if (c.ep[i] < 4) != (i < 4) and c.ep[i] < 8]
    out = []
    out.append(f"  中层棱在外: " + (", ".join(f"{a}(在{b}位)" for a, b in mids_out) or "无"))
    out.append(f"  反色棱: " + (", ".join(flipped) or "无") + f" (共{len(flipped)}条)")
    out.append(f"  顶底跑错层: " + (", ".join(wrong_layer) or "无"))
    return "\n".join(out)

# ---------------- formula lookup ----------------
def lookup_formula(c):
    key = " ".join(map(str, c.ep))
    with open("onelook_full.csv") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split(",")
            if parts[0] == key:
                return parts[1], parts[3], parts[4]
    return None

def main():
    scr = sys.argv[1] if len(sys.argv) > 1 else \
        "R' L U' R' B D B' L D' U D' F' B L' U F B' F' L F B' D' L B' R"
    print(f"打乱: {scr}\n")
    cube = apply_sequence(scr)

    # ① corners
    c_sol = solve_corners_cube(cube)
    for m in c_sol:
        cube.multiply(MOVES[m])
    assert cube.cp == list(range(8)) and cube.co == [0] * 8
    print(f"① 解8角(对齐中心) [{len(c_sol)}步]: {' '.join(c_sol)}")
    print(f"   -> 8角全对 ✓  剩余棱的状态:")
    print(narrate_edges(cube) + "\n")

    # ② stage B
    print("② 凑 · 子目标B: 中层棱归中层(带定向), 允许欠E账")
    libB = build_B_chunks()
    pathB = dijkstra_B(cube, libB, slice_done, max_moves=14)
    assert pathB is not None, "B stage not found"
    for seq, after, debt in pathB:
        cube.multiply(_effect(seq))
        assert cube == after
        owe = "账清" if debt == 0 else f"欠E×{debt}"
        print(f"   {' '.join(seq):12s} -> 角✓ {owe}")
        print(narrate_edges(cube))
    if not pathB:
        print("   已满足, 跳过")
    print()

    # ② stage A+C
    print("② 凑 · 子目标A+C: 清翻棱 + 顶底分层")
    libAC = build_AC_chunks()
    def score(c):
        wrong = sum(1 for i in range(8) if (c.ep[i] < 4) != (i < 4))
        return 2 * wrong + sum(c.eo[:8])
    pathAC = bfs_chunks(cube, libAC, ac_done, max_chunks=3)
    if pathAC is None:
        pathAC = beam_chunks(cube, libAC, ac_done, score)
    assert pathAC is not None, "A+C stage not found"
    for seq, after in pathAC:
        cube.multiply(_effect(seq))
        assert cube == after
        print(f"   {' '.join(seq):28s} -> 角✓中心✓")
        print(narrate_edges(cube))
    if not pathAC:
        print("   已满足, 跳过")
    print()

    # sanity: precondition reached
    assert (cube.cp == list(range(8)) and cube.co == [0] * 8
            and cube.eo == [0] * 12 and slice_done(cube) and ac_done(cube))
    print("   ★ 前置达成: 角全对 + 全棱定向 + 全棱回本层\n")

    # ③ formula
    r = lookup_formula(cube)
    assert r, "state not in table?!"
    cid, ln, formula = r
    print(f"③ 识别三层: U层[{_layer_str(cube,0)}] D层[{_layer_str(cube,4)}] E层[{_layer_str(cube,8)}]")
    print(f"   查表 -> {cid} [{ln}步]: {formula}")
    for m in formula.split():
        cube.multiply(MOVES[m])
    assert cube.is_solved()
    print(f"\n完全还原 ✓")

    nB = sum(len(s) for s, _, _ in pathB)
    nAC = sum(len(s) for s, _ in pathAC)
    print(f"步数: 角{len(c_sol)} + 凑({nB}+{nAC}) + 公式{ln} = "
          f"{len(c_sol) + nB + nAC + int(ln)}")

_EFF_CACHE = {}
def _effect(seq):
    k = tuple(seq)
    if k not in _EFF_CACHE:
        c = CubieCube(); apply_seq(c, seq)
        _EFF_CACHE[k] = c
    return _EFF_CACHE[k]

def _layer_str(c, base):
    from gen_onelook import cycles_str
    return cycles_str(list(c.ep), base)

if __name__ == "__main__":
    main()
