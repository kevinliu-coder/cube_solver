"""Strong pruning tables for the optimal-凑 search, built with numpy BFS.

Table 1: exact distance over (flip 2048) x (sep 34650)   [71 MB]
         sep = which layer-class (U/D/E) sits in each edge slot
Table 2: exact distance over (cperm 40320) x (twist 2187) [88 MB]

Both are BFS distances from the 凑 goal under all 18 face moves, so
max(t1, t2) is an admissible IDA* bound for
  flip=0, all edges in home layer, corners fully solved.
"""
import numpy as np, time, array
from math import comb
from cubie import CubieCube, MOVES
import coord as C
from tables import MOVE_NAMES

NSEP = 34650  # C(12,4) * C(8,4)

# ---- sep coordinate: rank the (U-class positions, D-class positions) ----
def sep_rank(classes):
    u_pos = [i for i in range(12) if classes[i] == 0]
    d_pos_rel = []
    rest = [i for i in range(12) if classes[i] != 0]
    for j, p in enumerate(rest):
        if classes[p] == 1:
            d_pos_rel.append(j)
    r1 = sum(comb(u_pos[i], i + 1) for i in range(4))
    r2 = sum(comb(d_pos_rel[i], i + 1) for i in range(4))
    return r1 * 70 + r2

def sep_unrank(idx):
    r1, r2 = divmod(idx, 70)
    def unrank_subset(r, n, k):
        pos = []
        for i in range(k - 1, -1, -1):
            p = i
            while comb(p + 1, i + 1) <= r:
                p += 1
            pos.append(p)
            r -= comb(p, i + 1)
        return sorted(pos)
    u_pos = unrank_subset(r1, 12, 4)
    rest = [i for i in range(12) if i not in u_pos]
    d_rel = unrank_subset(r2, 8, 4)
    classes = [2] * 12
    for p in u_pos:
        classes[p] = 0
    for j in d_rel:
        classes[rest[j]] = 1
    return classes

SEP_SOLVED = sep_rank([0]*4 + [1]*4 + [2]*4)

def build_sep_move():
    tbl = np.zeros((NSEP, 18), dtype=np.int32)
    for s in range(NSEP):
        cls = sep_unrank(s)
        for mi, mn in enumerate(MOVE_NAMES):
            mep = MOVES[mn].ep
            ncls = [cls[mep[i]] for i in range(12)]
            tbl[s, mi] = sep_rank(ncls)
    return tbl

def np_bfs(move_a, move_b, na, nb, start_a, start_b, name):
    t0 = time.time()
    dist = np.full(na * nb, 255, dtype=np.uint8)
    dist[start_a * nb + start_b] = 0
    d = 0
    while True:
        frontier = np.nonzero(dist == d)[0]
        if frontier.size == 0:
            break
        a, b = frontier // nb, frontier % nb
        for m in range(18):
            ni = move_a[a, m].astype(np.int64) * nb + move_b[b, m]
            mask = dist[ni] == 255
            dist[ni[mask]] = d + 1
        print(f"  {name} depth {d}: frontier {frontier.size}  ({time.time()-t0:.0f}s)",
              flush=True)
        d += 1
    return dist

def main():
    print("sep move table...", flush=True)
    sep_move = build_sep_move()
    np.save("sep_move.npy", sep_move)

    print("flip move table...", flush=True)
    flip_move = np.zeros((C.N_FLIP, 18), dtype=np.int32)
    for f in range(C.N_FLIP):
        base = CubieCube(); C.set_flip(base, f)
        for mi, mn in enumerate(MOVE_NAMES):
            cc = base.copy(); cc.edge_multiply(MOVES[mn])
            flip_move[f, mi] = C.get_flip(cc)

    print("BFS (flip x sep)...", flush=True)
    d1 = np_bfs(flip_move, sep_move, C.N_FLIP, NSEP, 0, SEP_SOLVED, "flip-sep")
    np.save("prun_flip_sep.npy", d1)
    print(f"  max dist {d1.max()}", flush=True)

    print("corner move tables from bins...", flush=True)
    a = array.array("H"); a.fromfile(open("cpm.bin", "rb"), C.N_CPERM * 18)
    cpm = np.frombuffer(a, dtype=np.uint16).reshape(C.N_CPERM, 18).astype(np.int32)
    a = array.array("H"); a.fromfile(open("twm.bin", "rb"), C.N_TWIST * 18)
    twm = np.frombuffer(a, dtype=np.uint16).reshape(C.N_TWIST, 18).astype(np.int32)

    print("BFS (cperm x twist)...", flush=True)
    d2 = np_bfs(cpm, twm, C.N_CPERM, C.N_TWIST, 0, 0, "corner")
    np.save("prun_corner_full.npy", d2)
    print(f"  max dist {d2.max()}", flush=True)
    print("done")

if __name__ == "__main__":
    main()
