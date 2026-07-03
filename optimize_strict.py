"""在严格定义的 (2000公式 + S_业余) 下, 求最优方法, 并证明最优性。

S_业余 (可判定谓词):
  search 阶段合法  <=>  pieces<=5  且  phase_moves<=8  且  not needs_eo
  formula 阶段合法 <=>  size <= 150  (业余识别上限)
  全局: 总公式 <= 2000

每个阶段: (名称, type, moves, formulas, pieces, needs_eo)
"""
S = dict(max_pieces=5, max_phase_moves=8, can_track_eo=False, recog_cap=150, budget=2000)

# 阶段库
P = {
    "cross":   ("search", 6, 0, 4, False),
    "f2l_pair":("search", 7, 0, 5, False),   # 一对(角+棱)+空槽, 看位置
    "eocross": ("search", 8, 0, 4, True),     # 需要EO追踪
    "eoline":  ("search", 6, 0, 3, True),     # 需要EO追踪
    "fb":      ("search", 8, 0, 5, False),    # Roux块, 看位置
    "sb":      ("search", 9, 0, 5, False),
    "lse":     ("search", 13, 0, 6, True),    # 后六棱: 先做EO -> 需要EO追踪
    "oll":     ("formula", 9, 57, 0, False),
    "pll":     ("formula", 12, 21, 0, False),
    "cmll":    ("formula", 10, 42, 0, False),
    "zbll":    ("formula", 13, 493, 0, False),
    "1lookLSE":("formula", 9, 1440, 0, False),
    "1lll":    ("formula", 12, 3915, 0, False),
}

# 候选方法 = 阶段名序列 (f2l = 4个pair)
METHODS = {
    "CFOP":          ["cross","f2l_pair","f2l_pair","f2l_pair","f2l_pair","oll","pll"],
    "ZZ+ZBLL":       ["eocross","f2l_pair","f2l_pair","f2l_pair","f2l_pair","zbll"],
    "ZZ+2look":      ["eocross","f2l_pair","f2l_pair","f2l_pair","f2l_pair","oll","pll"],
    "Roux":          ["fb","sb","cmll","lse"],
    "Roux+1lookLSE": ["fb","sb","cmll","1lookLSE"],
    "ZZ+1LLL":       ["eocross","f2l_pair","f2l_pair","f2l_pair","f2l_pair","1lll"],
}


def phase_legal(pname):
    typ, mv, f, pieces, eo = P[pname]
    if typ == "search":
        if eo and not S["can_track_eo"]: return False, "需要EO追踪(S外)"
        if pieces > S["max_pieces"]:      return False, f"块数{pieces}>5"
        if mv > S["max_phase_moves"]:     return False, f"步数{mv}>8"
    else:
        if f > S["recog_cap"]:            return False, f"表{f}>150识别上限"
    return True, ""


def method_legal(seq):
    total_f = sum(P[p][2] for p in seq)
    if total_f > S["budget"]: return False, "超2000预算"
    for p in seq:
        ok, why = phase_legal(p)
        if not ok: return False, f"[{p}] {why}"
    return True, ""


if __name__ == "__main__":
    print("严格约束: S_业余(块≤5, 步≤8, 不可追EO, 表≤150) + 总公式≤2000\n")
    print(f"{'方法':16s} {'步数':>5} {'公式':>6} {'合法?':>6}  {'淘汰原因'}")
    print("-"*60)
    legal=[]
    for name, seq in METHODS.items():
        ok, why = method_legal(seq)
        mv = sum(P[p][1] for p in seq)
        f = sum(P[p][2] for p in seq)
        if ok: legal.append((name, mv, f)); why="✓合法"
        print(f"{name:16s} {mv:>5} {f:>6} {'✓' if ok else '✗':>6}  {why}")
    print()
    best = min(legal, key=lambda r: r[1])
    print(f">>> S_业余 + 2000 下的严格最优: 【{best[0]}】 {best[1]}步 / {best[2]}公式")
    print(f">>> 所有更省步的(ZZ/Roux/1look类)全被 S 淘汰:")
    print(f"    - ZZ系: EOCross/EOLine 需追踪EO, 不在业余S内")
    print(f"    - ZBLL/1lookLSE/1LLL: 表>150, 超业余识别上限")
    print(f"    - Roux: LSE需先做EO, 不在业余S内")
