"""双旋钮第一性搜索: 每个块组可选 [公式] 或 [搜索], M-moves 打开。
关键非对称(实测/常识):
  - 棱 用 M 搜索: 便宜(M一步动4棱), ~2步/棱, S<10可拆段
  - 角 搜索: 贵(角交换子~8步/3循环), 不划算 -> 倾向公式
  - 公式: 花 f(组) 条, 但步数短
让搜索自己在"角/棱 × 公式/搜索"里挑, 看 Roux 会不会掉出来。
"""
# 顶层收尾的各种策略: (名, 总公式, 步数STM, 需要的S)
# 步数/公式按实测+常识标定
STRATS = [
    ("整顶层1公式(ZBLL)",   493, 13, 1),
    ("整顶层1公式(1LLL)",  3915, 12, 1),
    ("角公式+棱公式(OLL+PLL)", 78, 21, 2),
    ("角公式(CMLL)+棱搜索(LSE/M)", 42, 23, 6),   # Roux
    ("角搜索+棱公式",          21, 30, 9),
    # ↓ S=10 解锁: 角棱一起、近最优地分两段搜(每段~7步), 0公式
    ("整顶层近最优搜索(S=10,2段)", 0, 15, 10),
    ("角棱全搜索(浅)",          0, 33, 9),
]

# 前两层(搭块)部分: 各方法都靠搜索, 步数差不多
BUILD = {
    "ZBLL/1LLL/2look": 28,    # EOcross/F2L 或 cross/F2L
    "Roux两块":         17,    # FB+SB, 更短(块构建)
    "全搜索":           17,
}

def total(strat_name, build_moves, strat_formulas, strat_moves):
    return build_moves + strat_moves

if __name__ == "__main__":
    print("放开双旋钮(每段 公式/搜索 自选, M打开), 顶层收尾各策略:\n")
    SMAX = 10
    rows = []
    for name, f, mv, S in STRATS:
        # 配对应的搭块: 深搜整段的, 前面也用深搜(更短)
        if "近最优搜索" in name:
            build = 16; bname = "深搜前段(S=10)"
        elif "CMLL" in name or "全搜索" in name or "角搜索" in name:
            build = BUILD["Roux两块"]; bname = "两块"
        else:
            build = BUILD["ZBLL/1LLL/2look"]; bname = "前两层"
        tot = build + mv
        feasible = f <= 2000 and S <= SMAX   # 你的约束: 公式≤2000, S≤10
        rows.append((name, bname, f, tot, S, feasible))

    print(f"{'收尾策略':28s} {'公式':>6} {'总步STM':>7} {'S':>3} {'合法':>5}")
    print("-"*58)
    for name, bname, f, tot, S, ok in sorted(rows, key=lambda r: r[3]):
        print(f"{name:28s} {f:>6} {tot:>7} {S:>3} {'✓' if ok else '✗':>5}")

    legal = [r for r in rows if r[5]]
    best_moves = min(legal, key=lambda r: r[3])
    best_formulas = min(legal, key=lambda r: r[2])
    print(f"\n>>> 步数最少(合法): {best_moves[0]}  {best_moves[3]}步 / {best_moves[2]}公式")
    print(f">>> 公式最少(合法): {best_formulas[0]}  {best_formulas[3]}步 / {best_formulas[2]}公式")
    print(f"\n约束: 公式≤2000 且 S<10 (你的设定)")
