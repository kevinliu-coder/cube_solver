"""三阶段子群链求解器 (Thistlethwaite 4 阶段合并末两段为 3 阶段)。

阶段1: G0 -> G1=<U,D,L,R,F2,B2>     棱块全定向 (flip=0)            [18 步可用]
阶段2: G1 -> G2=<U,D,L2,R2,F2,B2>   角块定向+中层棱归位 (twist=0,slice) [14 步可用]
阶段3: G2 -> e                       完全还原 (cperm=eperm=sperm=0)    [10 步可用]

每阶段用 IDA* 求该阶段最短解 (optimal-per-stage, 经典 Thistlethwaite 做法),
拼接即为总解。用来量化「3 阶段 vs 2 阶段(19.4)」的步数差距。
"""
from __future__ import annotations
import os, pickle, time
from cubie import CubieCube, MOVES, apply_sequence
import coord as C
from tables import load, MOVE_NAMES, PHASE2_IDX, _bfs_prune

# 各阶段允许的转动 (索引进 MOVE_NAMES)
# 顺序: U U2 U' R R2 R' F F2 F' D D2 D' L L2 L' B B2 B'
G0_IDX = list(range(18))
G1_IDX = [0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 13, 14, 16]  # 去掉 F,F',B,B' (F/B 仅半转)
G2_IDX = PHASE2_IDX  # U U2 U' R2 F2 D D2 D' L2 B2

EXTRA_CACHE = os.path.join(os.path.dirname(__file__), "tables_thistle3.pkl")
_T = None      # 主表
_E = None       # 额外表 (flip 剪枝, twist/slice@G1 剪枝)


def _extra():
    global _E
    if _E is not None:
        return _E
    if os.path.exists(EXTRA_CACHE):
        with open(EXTRA_CACHE, "rb") as f:
            _E = pickle.load(f)
        return _E
    T = load()
    print("building stage-1/2 pruning tables (一次性)...")
    t0 = time.time()
    # 阶段1: flip -> 0, 全 18 步。用单坐标 BFS (n_b=1 占位)
    one = [[0] * 18]  # dummy second coord, always 0
    flip_move = T["flip_move"]
    prun_flip = _bfs_prune(C.N_FLIP, 1, flip_move, one, 18, 0, 0)
    # 阶段2: (twist, slice) -> (0, SLICE_SOLVED), 仅 14 个 G1 步
    tw14 = [[T["twist_move"][t][m] for m in G1_IDX] for t in range(C.N_TWIST)]
    sl14 = [[T["slice_move"][s][m] for m in G1_IDX] for s in range(C.N_SLICE)]
    prun_tw_sl_g1 = _bfs_prune(C.N_TWIST, C.N_SLICE, tw14, sl14, 14, 0, C.SLICE_SOLVED)
    _E = dict(prun_flip=prun_flip, prun_tw_sl_g1=prun_tw_sl_g1, tw14=tw14, sl14=sl14)
    with open(EXTRA_CACHE, "wb") as f:
        pickle.dump(_E, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"  done ({time.time()-t0:.1f}s), cached")
    return _E


def _opposite(face):
    return (face + 3) % 6

def _allowed(face, last1, last2):
    if last1 == -1:
        return True
    if face == last1:
        return False
    if last2 != -1 and face == last2 and _opposite(face) == last1:
        return False
    return True


def _ida_stage(start_coords, move_tables, goal, move_idx, n_moves, prune_fn, max_len=20):
    """通用单阶段 IDA*。返回 MOVE_NAMES 索引序列。
    start_coords/goal: tuple of coordinate values
    move_tables: list of per-coord move tables (each indexed [coord][local_move_idx])
    move_idx: list mapping local idx -> MOVE_NAMES idx (用于取 face)
    prune_fn(coords)-> 下界
    """
    sol = []
    ncoord = len(start_coords)

    def search(coords, depth, bound, last1, last2):
        lb = prune_fn(coords)
        if depth + lb > bound:
            return None
        if coords == goal:
            return list(sol) if lb == 0 else None
        for li in range(n_moves):
            face = move_idx[li] // 3
            if not _allowed(face, last1, last2):
                continue
            nc = tuple(move_tables[c][coords[c]][li] for c in range(ncoord))
            sol.append(move_idx[li])
            r = search(nc, depth + 1, bound, face, last1)
            if r is not None:
                return r
            sol.pop()
        return None

    for bound in range(prune_fn(start_coords), max_len + 1):
        sol.clear()
        r = search(start_coords, 0, bound, -1, -1)
        if r is not None:
            return r
    return None


def _stage_solutions(start, move_tables, goal, move_idx, n_moves, prune_fn, max_len, deadline):
    """生成器:按长度递增 yield 该阶段所有解 (MOVE_NAMES 索引序列)。"""
    sol = []
    ncoord = len(start)

    def search(coords, depth, bound, last1, last2):
        if time.time() > deadline:
            return
        lb = prune_fn(coords)
        if depth + lb > bound:
            return
        if coords == goal:
            if depth == bound:
                yield list(sol)
            return
        for li in range(n_moves):
            face = move_idx[li] // 3
            if not _allowed(face, last1, last2):
                continue
            nc = tuple(move_tables[c][coords[c]][li] for c in range(ncoord))
            sol.append(move_idx[li])
            yield from search(nc, depth + 1, bound, face, last1)
            sol.pop()

    for bound in range(prune_fn(start), max_len + 1):
        if time.time() > deadline:
            return
        yield from search(start, 0, bound, -1, -1)


def solve3_opt(scramble, timeout=10.0, eo_slack=2, s2_slack=2):
    """多解优化版 3 阶段:每段尝试 [最优, 最优+slack] 内的多个解,联合最小化总步数。
    返回 (solution_str, total, [n1, n2, n3])。"""
    T = load(); E = _extra()
    cube0 = apply_sequence(scramble)
    if cube0.is_solved():
        return "", 0, [0, 0, 0]
    deadline = time.time() + timeout
    pf = E["prun_flip"]; ptss = E["prun_tw_sl_g1"]; NS = C.N_SLICE
    pcs = T["prun_cperm_sperm"]; pes = T["prun_eperm_sperm"]; NSP = C.N_SPERM
    cm, em, smv = T["cperm_move"], T["eperm_move"], T["sperm_move"]

    flip0 = C.get_flip(cube0)
    best = None
    best_len = 99

    for s1 in _stage_solutions((flip0,), [T["flip_move"]], (0,), G0_IDX, 18,
                               lambda c: pf[c[0]], pf[flip0] + eo_slack, deadline):
        if time.time() > deadline:
            break
        cube1 = cube0.copy()
        for m in s1:
            cube1.multiply(MOVES[MOVE_NAMES[m]])
        tw, sl = C.get_twist(cube1), C.get_slice(cube1)
        s2_min = ptss[tw * NS + sl]
        if len(s1) + s2_min >= best_len:
            continue
        for s2 in _stage_solutions((tw, sl), [E["tw14"], E["sl14"]], (0, C.SLICE_SOLVED),
                                   G1_IDX, 14, lambda c: ptss[c[0] * NS + c[1]],
                                   s2_min + s2_slack, deadline):
            if len(s1) + len(s2) >= best_len:
                continue
            cube2 = cube1.copy()
            for m in s2:
                cube2.multiply(MOVES[MOVE_NAMES[m]])
            cp = C.get_corner_perm(cube2); ep = C.get_edge8_perm(cube2); sp = C.get_slice_perm(cube2)
            s3_lb = max(pcs[cp * NSP + sp], pes[ep * NSP + sp])
            if len(s1) + len(s2) + s3_lb >= best_len:
                continue
            s3 = _ida_stage((cp, ep, sp), [cm, em, smv], (0, 0, 0), G2_IDX, 10,
                            lambda c: max(pcs[c[0] * NSP + c[2]], pes[c[1] * NSP + c[2]]),
                            max_len=best_len - len(s1) - len(s2) - 1)
            if s3 is None:
                continue
            total = len(s1) + len(s2) + len(s3)
            if total < best_len:
                best_len = total
                best = (list(s1), list(s2), list(s3))

    if best is None:  # 超时未优化到,退回贪心
        return solve3(scramble)
    s1, s2, s3 = best
    moves = s1 + s2 + s3
    return " ".join(MOVE_NAMES[m] for m in moves), len(moves), [len(s1), len(s2), len(s3)]


def solve3(scramble):
    """3 阶段求解。返回 (solution_str, total, [n1, n2, n3])。"""
    T = load()
    E = _extra()
    cube = apply_sequence(scramble)
    if cube.is_solved():
        return "", 0, [0, 0, 0]
    moves_all = []

    # ---- 阶段1: flip -> 0, 全 18 步 ----
    pf = E["prun_flip"]
    s1 = _ida_stage(
        (C.get_flip(cube),),
        [T["flip_move"]],
        (0,), G0_IDX, 18,
        lambda c: pf[c[0]],
    )
    for m in s1:
        cube.multiply(MOVES[MOVE_NAMES[m]])
    moves_all += s1

    # ---- 阶段2: (twist, slice) -> (0, SLICE_SOLVED), 14 个 G1 步 ----
    ptss = E["prun_tw_sl_g1"]; NS = C.N_SLICE
    s2 = _ida_stage(
        (C.get_twist(cube), C.get_slice(cube)),
        [E["tw14"], E["sl14"]],
        (0, C.SLICE_SOLVED), G1_IDX, 14,
        lambda c: ptss[c[0] * NS + c[1]],
    )
    for m in s2:
        cube.multiply(MOVES[MOVE_NAMES[m]])
    moves_all += s2

    # ---- 阶段3: 完全还原, 10 个 G2 步 ----
    cm, em, smv = T["cperm_move"], T["eperm_move"], T["sperm_move"]
    pcs, pes = T["prun_cperm_sperm"], T["prun_eperm_sperm"]; NSP = C.N_SPERM
    s3 = _ida_stage(
        (C.get_corner_perm(cube), C.get_edge8_perm(cube), C.get_slice_perm(cube)),
        [cm, em, smv],
        (0, 0, 0), G2_IDX, 10,
        lambda c: max(pcs[c[0] * NSP + c[2]], pes[c[1] * NSP + c[2]]),
    )
    for m in s3:
        cube.multiply(MOVES[MOVE_NAMES[m]])
    moves_all += s3

    sol = " ".join(MOVE_NAMES[m] for m in moves_all)
    return sol, len(moves_all), [len(s1), len(s2), len(s3)]


def verify(scramble, solution):
    cube = apply_sequence(scramble)
    for mv in solution.split():
        cube.multiply(MOVES[mv])
    return cube.is_solved()


if __name__ == "__main__":
    import random
    load(); _extra()
    random.seed(42)
    print("\n3 阶段子群链 — 20 个随机打乱:\n")
    tot, st = [], [0, 0, 0]
    t0 = time.time()
    for n in range(20):
        scr = " ".join(random.choice(MOVE_NAMES) for _ in range(25))
        sol, k, br = solve3(scr)
        ok = verify(scr, sol)
        tot.append(k)
        for i in range(3): st[i] += br[i]
        print(f"#{n:2d}  共{k:2d}步  阶段[{br[0]}+{br[1]}+{br[2]}]  {'OK' if ok else 'BAD'}")
        assert ok
    print(f"\n平均 {sum(tot)/len(tot):.1f} 步 (最多{max(tot)}, 最少{min(tot)})")
    print(f"各阶段平均: 阶段1={st[0]/20:.1f}  阶段2={st[1]/20:.1f}  阶段3={st[2]/20:.1f}")
    print(f"对比基准: 2阶段 Kociemba = 19.4 步")
    print(f"({time.time()-t0:.1f}s)")
