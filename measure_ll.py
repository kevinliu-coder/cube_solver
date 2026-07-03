"""量出顶层"几条公式换几步"的真实曲线。

- 1-look 全顶层(1LLL): 随机顶层状态, 求(近)最优解, 平均步数。
- 这是 ~3915 条公式买到的步数。
对照不同收法的公式数(来自 lastlayer.py)即可看 ROI。
"""
import random
from cubie import CubieCube, MOVES
from twophase import solve_cube
from tables import load


def parity(p):
    par = 0
    for i in range(len(p)):
        for j in range(i + 1, len(p)):
            if p[i] > p[j]:
                par ^= 1
    return par


def random_ll_state(rng):
    """随机一个可达顶层状态(前两层已解)。"""
    while True:
        co = [rng.randrange(3) for _ in range(4)]
        if sum(co) % 3:
            continue
        eo = [rng.randrange(2) for _ in range(4)]
        if sum(eo) % 2:
            continue
        cp = list(range(4)); rng.shuffle(cp)
        ep = list(range(4)); rng.shuffle(ep)
        if parity(cp) != parity(ep):
            continue
        c = CubieCube()
        c.cp[0:4] = cp; c.co[0:4] = co
        c.ep[0:4] = ep; c.eo[0:4] = eo
        return c


if __name__ == "__main__":
    load()
    rng = random.Random(11)
    N = 60
    print(f"测量 1-look 全顶层(1LLL) 平均最优步数, 样本 {N}...\n")
    lens = []
    for i in range(N):
        c = random_ll_state(rng)
        sol, k = solve_cube(c.copy(), timeout=6.0)
        cc = c.copy()
        for m in sol.split():
            cc.multiply(MOVES[m])
        assert cc.is_solved(), f"#{i} 未还原"
        lens.append(k)
    lens.sort()
    avg = sum(lens) / N
    print(f"1-look 全顶层(1LLL, ~3915 条公式): 平均 {avg:.1f} 步  "
          f"(范围 {lens[0]}-{lens[-1]}, 中位 {lens[N//2]})")
    print(f"\n对照(社区已知 / 本仓库枚举):")
    print(f"  2-look  OLL+PLL   78 条公式 → ~18-20 步")
    print(f"  1-look  ZBLL     493 条公式 → ~12-13 步 (需棱已定向)")
    print(f"  1-look  1LLL    3915 条公式 → 实测上面这个数")
