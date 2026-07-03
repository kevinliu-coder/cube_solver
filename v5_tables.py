"""V5 速拧版全部公式表生成 + 逐条验证.

产出:
  v5_edge_table.txt   收棱表: G3内角已对的 6912 棱态 -> 视角折叠 (~880条)
  v5_corner_table.txt 先角表: 96 角态 -> 折叠 (~15条)
  v5_htr_table.txt    HTR表: 29400 陪集 -> 折叠 (~3700条, 按距离分级)
  v5_htr_full.csv     HTR机器全表
  v5_dr_triggers.txt  DR触发词典 (EO安全, 效果签名经引擎验证)
"""
import pickle, time
from collections import deque, Counter
from cubie import CubieCube, MOVES
import rotsym

EDGE_NAMES = ["UR","UF","UL","UB","DR","DF","DL","DB","FR","FL","BL","BR"]
CORNER_NAMES = ["URF","UFL","ULB","UBR","DFR","DLF","DBL","DRB"]
HALF = ["U2","D2","R2","L2","F2","B2"]
G1M = ["U","U2","U'","D","D2","D'","R2","L2","F2","B2"]

SYMS = rotsym.build_syms()

def pack(c):
    v = 0
    for x in c.cp: v = v * 8 + x
    for x in c.ep: v = v * 12 + x
    return v

# ---------- G3 machinery ----------
print("G3 BFS...", flush=True)
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
cd = {tuple(solved.cp): 0}
q = deque([solved])
while q:
    c = q.popleft()
    for m in HALF:
        c2 = c.copy(); c2.multiply(MOVES[m])
        k = tuple(c2.cp)
        if k not in cd:
            cd[k] = cd[tuple(c.cp)] + 1; q.append(c2)
print(f"  {len(G3D)} states, corners {len(cd)}  ({time.time()-t0:.0f}s)", flush=True)

def descend_full(cube):
    seq, c = [], cube.copy()
    while not c.is_solved():
        best = None
        for m in HALF:
            c2 = c.copy(); c2.multiply(MOVES[m])
            dd = G3D[pack(c2)]
            if best is None or dd < best[0]:
                best = (dd, m, c2)
        seq.append(best[1]); c = best[2]
    return seq

def descend_corners(cube):
    seq, c = [], cube.copy()
    while c.cp != list(range(8)):
        best = None
        for m in HALF:
            c2 = c.copy(); c2.multiply(MOVES[m])
            dd = cd[tuple(c2.cp)]
            if best is None or dd < best[0]:
                best = (dd, m, c2)
        seq.append(best[1]); c = best[2]
    return seq

def slice_cycles(ep, slots, tag):
    parts, seen = [], set()
    for s in slots:
        if s in seen or ep[s] == s:
            seen.add(s); continue
        cyc, j = [], s
        while j not in seen:
            seen.add(j); cyc.append(j); j = ep.index(ep[j]) if False else None
        break
    # simple mover list
    mv = [f"{EDGE_NAMES[ep[s]]}->{EDGE_NAMES[s]}" for s in slots if ep[s] != s]
    return f"{tag}:" + (",".join(mv) if mv else "好")

# ---------- 收棱表 ----------
print("edge table...", flush=True)
M_SLOTS, S_SLOTS, E_SLOTS = [1,3,5,7], [0,2,4,6], [8,9,10,11]
edge_states = {}
for k, d in G3D.items():
    pass
for c in G3CUBES:
    if c.cp == list(range(8)):
        edge_states[tuple(c.ep)] = c
assert len(edge_states) == 6912
canon, reps = {}, []
for key, c in edge_states.items():
    if key in canon: continue
    orbit = {}
    for si, (g, fmap) in enumerate(SYMS):
        cc = rotsym.conj(c, g)
        assert tuple(cc.cp) == tuple(range(8)) and cc.eo == [0]*12
        orbit.setdefault(tuple(cc.ep), si)
    rep = min(orbit)
    for k2 in orbit:
        canon.setdefault(k2, (rep, 0))
    reps.append(rep)
reps = sorted({r for r, _ in canon.values()})
# rebuild sym indices relative to the representative
canon = {}
for rep in reps:
    c = edge_states[rep]
    for si, (g, fmap) in enumerate(SYMS):
        k = tuple(rotsym.conj(c, g).ep)
        canon.setdefault(k, (rep, si))
assert len(canon) == 6912
rep_alg = {}
for rep in reps:
    c = edge_states[rep]
    alg = descend_full(c)
    v = c.copy()
    for m in alg: v.multiply(MOVES[m])
    assert v.is_solved()
    rep_alg[rep] = alg
# verify all 6912 via conjugated algs
for key, (rep, si) in canon.items():
    g, fmap = SYMS[si]
    alg = rotsym.map_alg(rep_alg[rep], fmap)
    v = edge_states[key].copy()
    for m in alg: v.multiply(MOVES[m])
    assert v.is_solved(), key
lens = [len(a) for a in rep_alg.values()]
print(f"  {len(reps)} classes, avg {sum(lens)/len(lens):.1f}, max {max(lens)}", flush=True)

with open("v5_edge_table.txt", "w") as f:
    f.write(f"V5 收棱表 — G3内、角已对, 全部180°转\n"
            f"识别: 三个切片各看4条棱怎么排 (M层=UF/UB/DF/DB位, S层=UR/UL/DR/DL位, E层=中层)\n"
            f"{len(reps)} 条核心 (覆盖全部6912态, 其余视角=整体转动后字母映射)\n"
            f"平均 {sum(lens)/len(lens):.1f} 步, 最长 {max(lens)}\n" + "="*90 + "\n\n")
    ids = {}
    for i, rep in enumerate(sorted(reps, key=lambda r: (len(rep_alg[r]), r)), 1):
        ids[rep] = i
        ep = list(rep)
        def desc(slots, tag):
            mv = [f"{EDGE_NAMES[ep[s]]}→{EDGE_NAMES[s]}" for s in slots if ep[s] != s]
            return f"{tag}[{' '.join(mv) if mv else '好'}]"
        f.write(f"E{i:03d} [{len(rep_alg[rep]):2d}步] "
                f"{desc(M_SLOTS,'M'):42s} {desc(S_SLOTS,'S'):42s} {desc(E_SLOTS,'E'):42s}\n"
                f"      {' '.join(rep_alg[rep])}\n\n")

# ---------- 先角表 ----------
print("corner table...", flush=True)
corner_states = {}
for cpk in cd:
    c = CubieCube(); c.cp = list(cpk)
    corner_states[cpk] = c
canon_c, reps_c = {}, []
for key, c in corner_states.items():
    if key in canon_c: continue
    orbit = {}
    for si, (g, fmap) in enumerate(SYMS):
        cc = rotsym.conj(c, g)
        orbit.setdefault(tuple(cc.cp), si)
    rep = min(orbit)
    for k2, si in orbit.items():
        canon_c.setdefault(k2, (rep, si))
    reps_c.append(rep)
reps_c = sorted({r for r, _ in canon_c.values()})
with open("v5_corner_table.txt", "w") as f:
    f.write(f"V5 先角表 — HTR后先把8角对号, 全部180°转 ({len(reps_c)}条核心, 覆盖96态)\n"
            + "="*80 + "\n\n")
    for i, rep in enumerate(sorted(reps_c, key=lambda r: cd[r]), 1):
        c = corner_states[rep]
        alg = descend_corners(c)
        v = c.copy()
        for m in alg: v.multiply(MOVES[m])
        assert v.cp == list(range(8))
        mv = [f"{CORNER_NAMES[c.cp[j]]}→{CORNER_NAMES[j]}" for j in range(8) if c.cp[j] != j]
        f.write(f"C{i:02d} [{len(alg)}步] {'  '.join(mv) if mv else '已对'}\n"
                f"     {' '.join(alg) if alg else '(无)'}\n\n")
print(f"  {len(reps_c)} classes", flush=True)

# ---------- HTR 表 ----------
print("HTR table...", flush=True)
with open("htr_coset.pkl", "rb") as f:
    H = pickle.load(f)
CPS, EPS, CID, EID = H["CPS"], H["EPS"], H["cid"], H["eid"]
CTRANS, ETRANS, HDIST = H["ctrans"], H["etrans"], H["dist"]

def coset_ids(c):
    kc = min(tuple(g[c.cp[i]] for i in range(8)) for g in CPS)
    ke = min(tuple(g[c.ep[i]] for i in range(12)) for g in EPS)
    return CID[kc], EID[ke]

def htr_formula(a, b):
    seq = []
    while HDIST[(a, b)] > 0:
        d = HDIST[(a, b)]
        for mi, m in enumerate(G1M):
            k = (CTRANS[a][mi], ETRANS[b][mi])
            if HDIST[k] == d - 1:
                seq.append(m); a, b = k
                break
    return seq

# enumerate one representative STATE per coset via table-driven BFS
coset_rep = {(0, 0): solved.copy()}
frontier = [((0, 0), solved.copy())]
while frontier:
    nxt = []
    for (a, b), c in frontier:
        for mi, m in enumerate(G1M):
            k = (CTRANS[a][mi], ETRANS[b][mi])
            if k not in coset_rep:
                c2 = c.copy(); c2.multiply(MOVES[m])
                coset_rep[k] = c2
                nxt.append((k, c2))
    frontier = nxt
print(f"  coset reps: {len(coset_rep)}  ({time.time()-t0:.0f}s)", flush=True)

# symmetry action tables on coset ids (conjugation by the 8 viewing angles)
CKEYS = {v: k for k, v in CID.items()}   # id -> canonical cp tuple
EKEYS = {v: k for k, v in EID.items()}   # id -> canonical ep tuple
ASYM, ESYM = [], []
for si, (g, fmap) in enumerate(SYMS):
    arow = [0] * len(CID)
    for a, kc in CKEYS.items():
        cc = CubieCube(); cc.cp = list(kc)
        arow[a] = CID[min(tuple(gg[rotsym.conj(cc, g).cp[i]] for i in range(8)) for gg in CPS)]
    erow = [0] * len(EID)
    for b, ke in EKEYS.items():
        cc = CubieCube(); cc.ep = list(ke)
        erow[b] = EID[min(tuple(gg[rotsym.conj(cc, g).ep[i]] for i in range(12)) for gg in EPS)]
    ASYM.append(arow); ESYM.append(erow)
print(f"  sym tables built  ({time.time()-t0:.0f}s)", flush=True)

canon_h, reps_h = {}, []
for key in coset_rep:
    if key in canon_h: continue
    orbit = {(ASYM[si][key[0]], ESYM[si][key[1]]) for si in range(8)}
    rep = min(orbit)
    for k2 in orbit:
        canon_h.setdefault(k2, (rep, 0))
    reps_h.append(rep)
reps_h = sorted({r for r, _ in canon_h.values()})
canon_h = {}
for rep in reps_h:
    for si in range(8):
        canon_h.setdefault((ASYM[si][rep[0]], ESYM[si][rep[1]]), (rep, si))
print(f"  {len(reps_h)} classes after folding", flush=True)

G3SET = set(G3D)
n_verified = 0
rows = []
for (a, b) in reps_h:
    alg = htr_formula(a, b)
    c = coset_rep[(a, b)].copy()
    for m in alg: c.multiply(MOVES[m])
    assert pack(c) in G3SET, (a, b)
    n_verified += 1
    rep = coset_rep[(a, b)]
    # bad corners: positions whose corner is not reachable within corner tetrad
    mix = sum(1 for i in S_SLOTS if rep.ep[i] in (1,3,5,7)) + \
          sum(1 for i in M_SLOTS if rep.ep[i] in (0,2,4,6))
    rows.append((len(alg), a, b, mix, alg, rep))
rows.sort()
with open("v5_htr_table.txt", "w") as f:
    f.write(f"V5 HTR表 — DR后凑到六面两色化, 转动: U D R2 L2 F2 B2\n"
            f"公式只依赖陪集类(角类+棱类), 同类任何状态通用\n"
            f"{len(rows)} 条核心 (覆盖29400陪集; 其余视角=整体转动映射)\n"
            f"分级: ★核心(≤6步) / ○常用(7-8) / ·长尾(9+)\n" + "="*90 + "\n\n")
    for i, (L, a, b, mix, alg, rep) in enumerate(rows, 1):
        tier = "★" if L <= 6 else ("○" if L <= 8 else "·")
        cmoved = [f"{CORNER_NAMES[rep.cp[j]]}→{CORNER_NAMES[j]}" for j in range(8) if rep.cp[j] != j]
        f.write(f"H{i:04d}{tier}[{L:2d}步] 角类{a:3d} 棱类{b:3d} 棱混轴{mix}条\n"
                f"      示例态 角:{' '.join(cmoved) if cmoved else '好'}\n"
                f"      {' '.join(alg) if alg else '(已是HTR)'}\n\n")
with open("v5_htr_full.csv", "w") as f:
    f.write("corner_class,edge_class,canonical_a,canonical_b,sym,length\n")
    for key, (rep, si) in canon_h.items():
        L = HDIST[key]
        f.write(f"{key[0]},{key[1]},{rep[0]},{rep[1]},{si},{L}\n")
tiers = Counter("★" if r[0] <= 6 else ("○" if r[0] <= 8 else "·") for r in rows)
print(f"  verified {n_verified}; tiers: {dict(tiers)}", flush=True)

# ---------- DR 触发词典 ----------
print("DR triggers...", flush=True)
TRIGGERS = ["R U R'", "R U' R'", "R U2 R'", "L' U' L", "L' U L", "L' U2 L",
            "R D R'", "R D' R'", "L' D L", "R U2 R' U2 R", "R' U R",
            "F2 R F2", "R", "R'", "L", "L'"]
with open("v5_dr_triggers.txt", "w") as f:
    f.write("V5 DR触发词典 — EO后凑角定向+中层, 全部EO安全\n"
            "签名: 哪些角位被拧(+顺/-逆), 中层位怎么动\n" + "="*80 + "\n\n")
    for t in TRIGGERS:
        c = CubieCube()
        ok = True
        for m in t.split():
            if m[0] in "FB" and m[1:] in ("", "'"):
                ok = False; break
            c.multiply(MOVES[m])
        assert ok and all(e == 0 for e in c.eo), t  # EO safe
        tw = [f"{CORNER_NAMES[j]}{'+' if c.co[j]==1 else '-'}" for j in range(8) if c.co[j] != 0]
        sl = [f"{EDGE_NAMES[c.ep[j]]}→{EDGE_NAMES[j]}" for j in range(8, 12) if c.ep[j] != j or c.ep[j] < 8]
        sl = [f"{EDGE_NAMES[c.ep[j]]}→{EDGE_NAMES[j]}" for j in range(12) if c.ep[j] != j and (j >= 8 or c.ep[j] >= 8)]
        f.write(f"{t:16s} 拧角: {' '.join(tw) if tw else '无':40s} 中层交换: {' '.join(sl) if sl else '无'}\n")
print("done. all tables written.", flush=True)
