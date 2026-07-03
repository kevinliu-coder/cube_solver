"""实测 v2: 强剪枝版. 需先运行 build_cou_tables.py.

剪枝 = max( 精确距离(flip x sep), 精确距离(cperm x twist) ), 两张表都是
到凑目标(全棱定向+全棱回本层+角全对)的可采纳下界.
"""
import random, time, sys
import numpy as np
from cubie import CubieCube, MOVES, apply_sequence
import coord as C
from tables import load, MOVE_NAMES, PHASE2_NAMES
from twophase import _solve_phase2
from build_cou_tables import NSEP, SEP_SOLVED, sep_rank

print("loading tables...", flush=True)
T = load()
FLIP_MOVE = T["flip_move"]
SEP_MOVE = [list(r) for r in np.load("sep_move.npy")]
PFS = bytes(np.load("prun_flip_sep.npy"))
PCF = bytes(np.load("prun_corner_full.npy"))
NT = C.N_TWIST

import array as _arr
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
        f = g + PCF[cp * NT + tw]
        if f > bound: return False
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

def get_sep(cube):
    return sep_rank([0 if e < 4 else (1 if e < 8 else 2) for e in cube.ep])

def optimal_cou(cube, max_depth=16, deadline=None):
    fl0, sp0 = C.get_flip(cube), get_sep(cube)
    cp0, tw0 = C.get_corner_perm(cube), C.get_twist(cube)
    sol = []
    nodes = [0]

    def h(fl, sp, cp, tw):
        a = PFS[fl * NSEP + sp]
        b = PCF[cp * NT + tw]
        return a if a > b else b

    def search(fl, sp, cp, tw, depth, bound, last):
        nodes[0] += 1
        if deadline and nodes[0] % 50000 == 0 and time.time() > deadline:
            raise TimeoutError
        lb = h(fl, sp, cp, tw)
        if depth + lb > bound:
            return False
        if lb == 0 and fl == 0 and sp == SEP_SOLVED and cp == 0 and tw == 0:
            return True
        for mi in range(18):
            if last >= 0 and mi // 3 == last // 3:
                continue
            sol.append(mi)
            if search(FLIP_MOVE[fl][mi], SEP_MOVE[sp][mi],
                      CPM[cp][mi], TWM[tw][mi], depth + 1, bound, mi):
                return True
            sol.pop()
        return False

    for bound in range(h(fl0, sp0, cp0, tw0), max_depth + 1):
        sol.clear()
        try:
            if search(fl0, sp0, cp0, tw0, 0, bound, -1):
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
        c_sol = solve_corners_cube(cube)
        for m in c_sol:
            cube.multiply(MOVES[m])
        assert cube.cp == list(range(8)) and cube.co == [0] * 8

        t0 = time.time()
        cou = optimal_cou(cube, deadline=time.time() + 300)
        dt = time.time() - t0
        if cou is None:
            print(f"#{k:2d} 角{len(c_sol):2d} 凑: 超时 ({dt:.0f}s)", flush=True)
            continue
        c2 = cube.copy()
        for m in cou:
            c2.multiply(MOVES[m])
        assert (c2.eo == [0] * 12 and get_sep(c2) == SEP_SOLVED
                and c2.cp == list(range(8)) and c2.co == [0] * 8)

        f_sol = _solve_phase2(c2, 18, time.time() + 120)
        formula = [PHASE2_NAMES[i] for i in f_sol]
        c3 = c2.copy()
        for m in formula:
            c3.multiply(MOVES[m])
        assert c3.is_solved()

        total = len(c_sol) + len(cou) + len(formula)
        rows.append((len(c_sol), len(cou), len(formula), total))
        print(f"#{k:2d} 角{len(c_sol):2d} + 凑{len(cou):2d} + 公式{len(formula):2d} "
              f"= 总{total:2d}   ({dt:.0f}s)", flush=True)

    if rows:
        n_ok = len(rows)
        avg = [sum(r[i] for r in rows) / n_ok for i in range(4)]
        mx = [max(r[i] for r in rows) for i in range(4)]
        mn = [min(r[i] for r in rows) for i in range(4)]
        print(f"\n=== {n_ok} 个样本 ===", flush=True)
        for i, nm in enumerate(["角", "凑", "公式", "总"]):
            print(f"{nm}:   平均 {avg[i]:.1f}  范围 {mn[i]}-{mx[i]}", flush=True)

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
