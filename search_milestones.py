"""真·第一性: 穷举"留给公式的末尾块集 U=(c角,e棱)", 算 f(U), 自己搜最优里程碑。
不预设任何方法/块结构。U 一旦定, 中介里程碑 = "搜索搭出 U 的补集"(D内自由切, 不影响步数)。

f(U): 补集已解时, U 这 c角+e棱 的不同配置数。
  角向自由度 3^(c-1)(c>=1), 棱向 2^(e-1)(e>=1), 置换 c!*e!/2(偶), 再 /对称.
move 模型(标定): build(p)=搜索搭 p=20-c-e 个块; finish(c,e)=一步收 U.
"""
from math import factorial

# 对称因子按已知精确值标定: LL(4,4)真值3915, 6棱(0,6)真值1440, 故 /≈12~16
SYM = 12

def f_U(c, e):
    if c == 0 and e == 0: return 1
    co = 3**(c-1) if c >= 1 else 1
    eo = 2**(e-1) if e >= 1 else 1
    perm = factorial(c) * factorial(e)
    perm = perm // 2 if perm >= 2 else perm
    raw = co * eo * perm
    return max(1, raw // SYM)

def build_moves(p):           # 搜索搭 p 个块(块越多越纠缠, 超线性)
    return round(p + 0.06 * p * p)

def finish_moves(c, e):       # 一步收 c+e 个块
    n = c + e
    return round(1.4 * n + 3) if n > 0 else 0


def search(R, budget=2000):
    best = None
    valid = []
    for c in range(0, 9):
        for e in range(0, 13):
            if c + e == 0 or c + e >= 12: continue
            f = f_U(c, e)
            if f > R or f > budget: continue
            p = 20 - c - e
            tot = build_moves(p) + finish_moves(c, e)
            valid.append((c, e, f, tot))
            if best is None or tot < best[3]:
                best = (c, e, f, tot)
    return best, valid


if __name__ == "__main__":
    for R in [150, 1440]:
        best, valid = search(R)
        print(f"\n=== R={R}: 穷举所有 f(U)≤R 的末尾块集, 自己搜最优 ===")
        valid.sort(key=lambda x: x[3])
        print(f"{'U=(c角,e棱)':>12} {'f(U)':>6} {'总步数':>6}")
        for c, e, f, tot in valid[:8]:
            mark = "  <== 最优" if (c, e) == (best[0], best[1]) else ""
            print(f"{('('+str(c)+'角,'+str(e)+'棱)'):>12} {f:>6} {tot:>6}{mark}")
        print(f"合法末尾块集共 {len(valid)} 种(f爆炸把其余全排除)")
        print(f">>> 自搜最优里程碑: 留 {best[0]}角+{best[1]}棱 给公式, 其余搜索搭, 共 {best[3]} 步")
