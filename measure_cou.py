"""实测: 角解完后, "凑"到一看收前置(全棱定向+全棱回本层+角不动)最优需要几步.

对 N 个随机打乱:
  1. 最优解8角 (corner_solve IDA*)
  2. IDA* 在全部18种转动里找最短序列, 目标:
       eo 全 0, 每棱回本层, 角(置换+朝向)回到全对
  3. 到前置后查 phase-2 最优公式长度
输出: 凑步数分布 + 全流程(角+凑+公式)总步数.
"""
import random, time, sys
from cubie import CubieCube, MOVES, apply_sequence
import coord as C
from tables import load, MOVE_NAMES
from twophase import _solve_phase2

T = load()
FLIP_MOVE, SLICE_MOVE = T["flip_move"], T["slice_move"]
TWIST_MOVE = T["twist_move"]
P_FS, P_TS = T["prun_flip_slice"], T["prun_twist_slice"]
NS = C.N_SLICE

print("loading corner tables from cpm.bin/twm.bin...", flush=True)
import array as _arr, random as _rand

def _load_bin(path, n):
    a = _arr.array("H")
    with open(path, "rb") as f:
        a.fromfile(f, n * 18)
    return [a[i * 18:(i + 1) * 18] for i in range(n)]

CPM = _load_bin("cpm.bin", C.N_CPERM)
TWM = _load_bin("twm.bin", C.N_TWIST)

# spot-check the binary tables against the cubie engine
_rand.seed(0)
for _ in range(200):
    p, mi = _rand.randrange(C.N_CPERM), _rand.randrange(18)
    b = CubieCube(); C.set_corner_perm(b, p); b.corner_multiply(MOVES[MOVE_NAMES[mi]])
    assert CPM[p][mi] == C.get_corner_perm(b), "cpm.bin mismatch"
    t = _rand.randrange(C.N_TWIST)
    b = CubieCube(); C.set_twist(b, t); b.corner_multiply(MOVES[MOVE_NAMES[mi]])
    assert TWM[t][mi] == C.get_twist(b), "twm.bin mismatch"
print("  bins verified against engine (200 spot checks)", flush=True)

def _bfs(move, n, goal):
    d = bytearray([255]) * n
    d[goal] = 0
    fr = [goal]
    dep = 0
    while fr:
        nx = []; dep += 1
        for s in fr:
            row = move[s]
            for mi in range(18):
                ns = row[mi]
                if d[ns] == 255:
                    d[ns] = dep; nx.append(ns)
        fr = nx
    return d

PCP, PTW = _bfs(CPM, C.N_CPERM, 0), _bfs(TWM, C.N_TWIST, 0)

def solve_corners(scramble):
    cube = apply_sequence(scramble)
    cp, tw = C.get_corner_perm(cube), C.get_twist(cube)
    sol = []
    def h(cp, tw): return max(PCP[cp], PTW[tw])
    def search(cp, tw, g, bound, last):
        f = g + h(cp, tw)
        if f > bound: return f
        if cp == 0 and tw == 0: return -1
        mn = 99
        for mi in range(18):
            if last >= 0 and mi // 3 == last // 3: continue
            r = search(CPM[cp][mi], TWM[tw][mi], g + 1, bound, mi)
            if r == -1:
                sol.append(MOVE_NAMES[mi]); return -1
            if r < mn: mn = r
        return mn
    bound = h(cp, tw)
    while True:
        sol.clear()
        if search(cp, tw, 0, bound, -1) == -1:
            sol.reverse(); return sol
        bound += 1

# per-move edge-slot permutation for fast ep tracking
MOVE_EP = {m: MOVES[m].ep for m in MOVE_NAMES}

def separated(ep):
    return (ep[0] < 4 and ep[1] < 4 and ep[2] < 4 and ep[3] < 4
            and 4 <= ep[4] < 8 and 4 <= ep[5] < 8 and 4 <= ep[6] < 8 and 4 <= ep[7] < 8)

def optimal_cou(cube, max_depth=14, deadline=None):
    """Shortest sequence (18 moves) to the one-look precondition."""
    fl0, sl0 = C.get_flip(cube), C.get_slice(cube)
    cp0, tw0 = C.get_corner_perm(cube), C.get_twist(cube)
    ep0 = tuple(cube.ep)
    sol = []

    def h(fl, sl, cp, tw):
        a = P_FS[fl * NS + sl]
        b = P_TS[tw * NS + sl]
        c_ = PCP[cp]
        d = PTW[tw]
        return max(a, b, c_, d)

    def search(fl, sl, cp, tw, ep, depth, bound, last):
        if deadline and time.time() > deadline:
            raise TimeoutError
        lb = h(fl, sl, cp, tw)
        if depth + lb > bound:
            return False
        if fl == 0 and sl == C.SLICE_SOLVED and cp == 0 and tw == 0 and separated(ep):
            return depth == bound or True
        if depth == bound:
            return False
        for mi in range(18):
            if last >= 0 and mi // 3 == last // 3:
                continue
            mep = MOVE_EP[MOVE_NAMES[mi]]
            nep = tuple(ep[mep[i]] for i in range(12))
            sol.append(mi)
            if search(FLIP_MOVE[fl][mi], SLICE_MOVE[sl][mi],
                      CPM[cp][mi], TWM[tw][mi], nep, depth + 1, bound, mi):
                return True
            sol.pop()
        return False

    if fl0 == 0 and sl0 == C.SLICE_SOLVED and cp0 == 0 and tw0 == 0 and separated(ep0):
        return []
    for bound in range(1, max_depth + 1):
        sol.clear()
        try:
            if search(fl0, sl0, cp0, tw0, ep0, 0, bound, -1):
                return [MOVE_NAMES[i] for i in sol]
        except TimeoutError:
            return None
    return None

def main(n=20, seed=7):
    random.seed(seed)
    rows = []
    for k in range(n):
        scr = " ".join(random.choice(MOVE_NAMES) for _ in range(30))
        cube = apply_sequence(scr)
        c_sol = solve_corners(scr)
        for m in c_sol:
            cube.multiply(MOVES[m])
        assert cube.cp == list(range(8)) and cube.co == [0] * 8

        t0 = time.time()
        cou = optimal_cou(cube, deadline=time.time() + 120)
        dt = time.time() - t0
        if cou is None:
            print(f"#{k:2d} 角{len(c_sol):2d} 凑: 超时/超深 ({dt:.0f}s)")
            continue
        c2 = cube.copy()
        for m in cou:
            c2.multiply(MOVES[m])
        assert (c2.eo == [0] * 12 and separated(tuple(c2.ep))
                and c2.cp == list(range(8)) and c2.co == [0] * 8)

        from tables import PHASE2_NAMES
        f_sol = _solve_phase2(c2, 18, time.time() + 60)
        formula = [PHASE2_NAMES[i] for i in f_sol]
        c3 = c2.copy()
        for m in formula:
            c3.multiply(MOVES[m])
        assert c3.is_solved()

        total = len(c_sol) + len(cou) + len(formula)
        rows.append((len(c_sol), len(cou), len(formula), total))
        print(f"#{k:2d} 角{len(c_sol):2d} + 凑{len(cou):2d} + 公式{len(formula):2d} "
              f"= 总{total:2d}   ({dt:.0f}s)  凑: {' '.join(cou)}")

    if rows:
        n_ok = len(rows)
        avg = [sum(r[i] for r in rows) / n_ok for i in range(4)]
        mx = [max(r[i] for r in rows) for i in range(4)]
        print(f"\n=== {n_ok} 个样本 ===")
        print(f"角:   平均 {avg[0]:.1f}  最大 {mx[0]}")
        print(f"凑:   平均 {avg[1]:.1f}  最大 {mx[1]}")
        print(f"公式: 平均 {avg[2]:.1f}  最大 {mx[2]}")
        print(f"总:   平均 {avg[3]:.1f}  最大 {mx[3]}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
