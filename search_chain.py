"""第一性搜索: 把20块(8角12棱)分成有序的 k 组里程碑, S-胶水模型下求最优。
不限 k。每组 i 的局面种类 V_i = 在剩余槽里安放该组块的配置数(置换×朝向)。
  ∏ V_i = 全配置数(校验). 公式 N_i = V_i / (B(S) * sym).  Σ N_i <= 2000.
目标: 阶段越少步数越少 => 找"≤2000公式可行"的最小 k, 及其分块(里程碑)。
"""
from math import factorial as fac
from itertools import product

def P(n, k):  # 排列数 n!/(n-k)!
    r = 1
    for i in range(k): r *= (n - i)
    return r

CONSTRAINT = 12      # 朝向/奇偶约束: 全配置/真实 ≈ 12
def variety(avail_c, c, avail_e, e):
    return P(avail_c, c) * (3**c) * P(avail_e, e) * (2**e)

def B(S): return 13.3 ** S

# 按阶段给对称: 第一段色彩中立可用24重旋转; 之后朝向锁死, 只剩AUF=4
def sym_for_stage(i):
    return 24 if i == 0 else 4

def stage_formulas(group_varieties, S):
    k = len(group_varieties)
    return [group_varieties[i] / (B(S) * sym_for_stage(i)) / (CONSTRAINT ** (1/k))
            for i in range(k)]

def all_splits(total, k):
    if k == 1:
        yield (total,); return
    for first in range(0, total + 1):
        for rest in all_splits(total - first, k - 1):
            yield (first,) + rest

def search(k, S, budget=2000):
    best = None
    for cs in all_splits(8, k):
        for es in all_splits(12, k):
            if any(cs[i] + es[i] == 0 for i in range(k)): continue  # 空组无意义
            vs = []; ac, ae = 8, 12
            for i in range(k):
                vs.append(variety(ac, cs[i], ae, es[i]))
                ac -= cs[i]; ae -= es[i]
            Ns = stage_formulas(vs, S)
            total = sum(Ns)
            if total > budget: continue
            maxN = max(Ns)
            if best is None or total < best[0]:
                best = (total, cs, es, Ns, maxN)
    return best


if __name__ == "__main__":
    for S in (3, 4):
        print(f"\n===== S={S}(胶水{S}步), B(S)={B(S):,.0f} =====")
        for k in (2, 3, 4, 5):
            b = search(k, S)
            if b is None:
                print(f"  k={k}阶段: 无≤2000方案 (不可行)")
            else:
                total, cs, es, Ns, maxN = b
                groups = " | ".join(f"{cs[i]}角{es[i]}棱" for i in range(k))
                print(f"  k={k}阶段: 总公式{total:6.0f}  最大单表{maxN:5.0f}  分块[{groups}]")
        # 报告最小可行 k
        for k in (2,3,4,5):
            if search(k,S):
                b=search(k,S)
                print(f"  >>> S={S} 最少 {k} 阶段可行, 总公式{b[0]:.0f}, "
                      f"分块 {' | '.join(f'{b[1][i]}角{b[2][i]}棱' for i in range(k))}")
                break
