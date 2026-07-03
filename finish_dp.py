"""第一性: 枚举所有"末尾块集U"的收法, 对每个R求最优, 看最优到底用多少公式。
不引用方法名, 只用 (块集U -> 表大小f(U), 步数) 这些组合事实。

候选末尾结构(每个=搜索build + 一串公式表[(表大小,步数)]):
  表大小来自我们的枚举; build步数来自常识标定。
约束: 每张表 <= R(识别), 总公式 <= 2000。目标: 最少总步数。
"""

# 候选收尾结构: (名, build步数=搜索部分, [(表大小, 该表步数), ...])
# build 一致标定: 两块=17, F2L=28, EO-F2L=30, LSE搜索=13
CANDIDATES = [
    ("CFOP 2-look",        28,        [(57, 9), (21, 12)]),     # 49步 / 78
    ("ZZ + ZBLL",          30,        [(493, 13)]),             # 43步 / 493
    ("两块+顶角公式+棱搜索",  17 + 13,   [(42, 10)]),              # 40步 / 42 (=Roux)
    ("两块+顶角+一步收6棱",   17,        [(42, 10), (1440, 9)]),   # 36步 / 1482
    ("无脑1-look整顶层",     28,        [(3915, 12)]),            # 40步 / 3915
]


def best_for_R(R, budget=2000):
    best = None
    for name, build, tables in CANDIDATES:
        max_table = max(t[0] for t in tables)
        total_f = sum(t[0] for t in tables)
        if max_table > R:      continue   # 识别不了
        if total_f > budget:   continue   # 超预算
        moves = build + sum(t[1] for t in tables)
        if best is None or moves < best[1]:
            best = (name, moves, total_f)
    return best


if __name__ == "__main__":
    print("对每个识别容量 R, 最省步的收法 + 它实际用了多少公式:\n")
    print(f"{'R(识别上限)':>10}  {'最优收法':22s} {'步数':>5} {'用了公式':>8} {'用满2000?':>9}")
    print("-" * 64)
    for R in [80, 150, 300, 493, 800, 1440, 2000, 4000]:
        b = best_for_R(R)
        if b:
            used = b[2]
            full = "✗ 远没用满" if used < 1900 else "≈用满"
            print(f"{R:>10}  {b[0]:22s} {b[1]:>5} {used:>8} {full:>9}")
    print()
    print("结论(第一性): 任何R下, 最优收法用的公式都 < 1500, 从不用满2000。")
    print("  - 低R: 只能2-look(78条), 想用更多被R挡(大表认不了)。")
    print("  - 高R: 顶到1-look-6棱(1482条)。再想多花, 唯一更大的是1LLL(3915)->超2000预算。")
    print("  => '用满2000更好' 是错的: 多花的公式要么超R认不了, 要么增加look反而加步。")
