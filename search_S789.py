"""S=7,8,9 严格搜: 完整方法(搭块+收尾), 允许用满2000公式, 求步数最少。
每个方法 = (名, 总步STM, 公式, 需要的S, 需要的R识别上限)
步数为STM估算(M算1步); 公式来自实测枚举(CMLL42/ZBLL493/1lookLSE1440/1LLL3915)。
"""
METHODS = [
    # 名,                              步,  公式,  S需,  R需
    ("Roux + LSE搜索",                 40,   42,   7,   42),
    ("Roux + 1-look-LSE",              36, 1482,   7, 1440),   # 角公式+棱一步收(大表)
    ("ZZ + ZBLL",                      43,  493,   7,  493),
    ("ZZ + 2look(OLL+PLL)",            45,   78,   7,   57),
    ("整顶层近最优搜索",                 41,    0,   8,    1),   # LL分2段搜(S>=8)
    ("CFOP",                           49,   78,   3,   57),
    ("Roux + ZBLL收顶角棱",            38, 1482,   7, 1440),   # 另一种大表组合
]

def best(S, budget=2000, R_human=None):
    legal = [m for m in METHODS
             if m[2] <= S and m[3] <= budget and (R_human is None or m[4] <= R_human)]
    return min(legal, key=lambda m: m[1]) if legal else None

if __name__ == "__main__":
    print("=== 不限识别R, 公式≤2000, 求步数最少 ===\n")
    print(f"{'S':>3}  {'最优方法':22s} {'步STM':>6} {'用公式':>6}  {'用满2000?'}")
    print("-"*60)
    for S in (7, 8, 9, 10):
        b = best(S)
        ratio = f"{b[1]} ({100*b[1]/2000:.0f}%预算)" if False else ""
        full = "✗" if b[1] < 1900 else "≈满"
        print(f"{S:>3}  {b[0]:22s} {b[1]:>6} {b[2]:>6}  用了{b[2]}/2000")

    print("\n=== 加上人类识别上限 R≤500 (现实) ===\n")
    print(f"{'S':>3}  {'最优方法':22s} {'步STM':>6} {'用公式':>6}")
    print("-"*50)
    for S in (7, 8, 9, 10):
        b = best(S, R_human=500)
        print(f"{S:>3}  {b[0]:22s} {b[1]:>6} {b[2]:>6}")

    print("\n结论:")
    print("  不限R: S=7~10 最优都是 Roux+1-look-LSE, 36步, 用1482公式(74%预算)")
    print("    -> 你对: 多用公式(1482 vs 42)省4步. 但需R>=1440(超人识别)")
    print("  限R<=500(现实): 退回 Roux+LSE搜索, 40步, 仅42公式")
    print("    -> 现实人类: 公式用不满, 因为认不了1440条; 卡在Roux 40步/42公式")
