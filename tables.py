"""Move tables and pruning tables for the two-phase solver.

Each coordinate transition is a pure function of (coordinate, move), so we
precompute move tables once. Pruning tables hold the BFS distance from the
goal in a combined (coord_a, coord_b) space, giving an admissible lower bound
for IDA*. Everything is cached to tables.pkl after the first build.
"""
from __future__ import annotations
import os, pickle, time, array
from cubie import CubieCube, MOVES
import coord as C

# ---- move ordering ----
FACES = ["U", "R", "F", "D", "L", "B"]
MOVE_NAMES = [f + s for f in FACES for s in ["", "2", "'"]]  # 18 moves
# phase-2 allowed moves: U,U2,U', D,D2,D', R2,L2,F2,B2
PHASE2_NAMES = ["U", "U2", "U'", "R2", "F2", "D", "D2", "D'", "L2", "B2"]
PHASE2_IDX = [MOVE_NAMES.index(m) for m in PHASE2_NAMES]

CACHE = os.path.join(os.path.dirname(__file__), "tables.pkl")


def _build_move_table(n, get, setter, multiply_attr, move_list):
    """move_list = list of move indices into MOVE_NAMES."""
    tbl = [array.array("i", [0] * len(move_list)) for _ in range(n)]
    for c in range(n):
        base = CubieCube()
        setter(base, c)
        for mi, m_idx in enumerate(move_list):
            cc = base.copy()
            getattr(cc, multiply_attr)(MOVES[MOVE_NAMES[m_idx]])
            tbl[c][mi] = get(cc)
    return tbl


def _bfs_prune(n_a, n_b, a_move, b_move, n_moves, start_a, start_b):
    """BFS distance over combined coordinate space; returns bytearray."""
    size = n_a * n_b
    dist = bytearray(b"\xff" * size)
    start = start_a * n_b + start_b
    dist[start] = 0
    frontier = [start]
    depth = 0
    filled = 1
    while frontier:
        nxt = []
        d1 = depth + 1
        for idx in frontier:
            a, b = divmod(idx, n_b)
            am, bm = a_move[a], b_move[b]
            for mi in range(n_moves):
                ni = am[mi] * n_b + bm[mi]
                if dist[ni] == 255:
                    dist[ni] = d1
                    filled += 1
                    nxt.append(ni)
        frontier = nxt
        depth = d1
    return dist


def build():
    t0 = time.time()
    print("building move tables (phase 1)...")
    all18 = list(range(18))
    twist_move = _build_move_table(C.N_TWIST, C.get_twist, C.set_twist, "corner_multiply", all18)
    flip_move = _build_move_table(C.N_FLIP, C.get_flip, C.set_flip, "edge_multiply", all18)
    slice_move = _build_move_table(C.N_SLICE, C.get_slice, C.set_slice, "edge_multiply", all18)
    print(f"  done ({time.time()-t0:.1f}s)")

    print("building move tables (phase 2)...")
    cperm_move = _build_move_table(C.N_CPERM, C.get_corner_perm, C.set_corner_perm, "corner_multiply", PHASE2_IDX)
    eperm_move = _build_move_table(C.N_EPERM, C.get_edge8_perm, C.set_edge8_perm, "edge_multiply", PHASE2_IDX)
    sperm_move = _build_move_table(C.N_SPERM, C.get_slice_perm, C.set_slice_perm, "edge_multiply", PHASE2_IDX)
    print(f"  done ({time.time()-t0:.1f}s)")

    print("building pruning tables (phase 1)...")
    prun_twist_slice = _bfs_prune(C.N_TWIST, C.N_SLICE, twist_move, slice_move, 18, 0, C.SLICE_SOLVED)
    prun_flip_slice = _bfs_prune(C.N_FLIP, C.N_SLICE, flip_move, slice_move, 18, 0, C.SLICE_SOLVED)
    print(f"  done ({time.time()-t0:.1f}s)")

    print("building pruning tables (phase 2)...")
    prun_cperm_sperm = _bfs_prune(C.N_CPERM, C.N_SPERM, cperm_move, sperm_move, 10, 0, 0)
    prun_eperm_sperm = _bfs_prune(C.N_EPERM, C.N_SPERM, eperm_move, sperm_move, 10, 0, 0)
    print(f"  done ({time.time()-t0:.1f}s)")

    data = dict(
        twist_move=twist_move, flip_move=flip_move, slice_move=slice_move,
        cperm_move=cperm_move, eperm_move=eperm_move, sperm_move=sperm_move,
        prun_twist_slice=prun_twist_slice, prun_flip_slice=prun_flip_slice,
        prun_cperm_sperm=prun_cperm_sperm, prun_eperm_sperm=prun_eperm_sperm,
    )
    with open(CACHE, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"cached to {CACHE} ({time.time()-t0:.1f}s total)")
    return data


def load():
    if os.path.exists(CACHE):
        with open(CACHE, "rb") as f:
            return pickle.load(f)
    return build()


if __name__ == "__main__":
    data = build()
    # sanity: goal pruning distances are 0; max distances are plausible
    print("\nsanity:")
    print("  prun_twist_slice[goal] =", data["prun_twist_slice"][0 * C.N_SLICE + C.SLICE_SOLVED])
    print("  prun_flip_slice[goal]  =", data["prun_flip_slice"][0 * C.N_SLICE + C.SLICE_SOLVED])
    print("  prun_cperm_sperm[goal] =", data["prun_cperm_sperm"][0])
    print("  prun_eperm_sperm[goal] =", data["prun_eperm_sperm"][0])
    print("  max phase1 twist/slice dist =", max(data["prun_twist_slice"]))
    print("  max phase1 flip/slice  dist =", max(data["prun_flip_slice"]))
    print("  max phase2 cperm/sperm dist =", max(data["prun_cperm_sperm"]))
    print("  max phase2 eperm/sperm dist =", max(data["prun_eperm_sperm"]))
