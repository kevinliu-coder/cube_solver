"""对比: 3阶段贪心 vs 3阶段多解优化 vs 2阶段Kociemba。"""
import time, random
from tables import load, MOVE_NAMES
import thistle3 as T3
import twophase as TP

load(); T3._extra()
random.seed(7)
N = 15
scrambles = [" ".join(random.choice(MOVE_NAMES) for _ in range(25)) for _ in range(N)]

print(f"{N} 个随机打乱:\n")
print(f"{'#':>2}  {'3段贪心':>8}  {'3段优化':>8}  {'2段K':>6}")
g, o, k = [], [], []
gt = ot = kt = 0.0
for i, scr in enumerate(scrambles):
    t = time.time(); sg, kg, _ = T3.solve3(scr); gt += time.time() - t
    assert T3.verify(scr, sg)
    t = time.time(); so, ko, br = T3.solve3_opt(scr, timeout=8.0); ot += time.time() - t
    assert T3.verify(scr, so)
    t = time.time(); sk, kk = TP.solve(scr, timeout=8.0); kt += time.time() - t
    assert TP.verify(scr, sk)
    g.append(kg); o.append(ko); k.append(kk)
    print(f"{i:>2}  {kg:>8}  {ko:>8}  {kk:>6}   (3段优化分配 {br[0]}+{br[1]}+{br[2]})")

print(f"\n平均:  3段贪心={sum(g)/N:.1f}   3段优化={sum(o)/N:.1f}   2段Kociemba={sum(k)/N:.1f}")
print(f"耗时:  3段贪心={gt:.1f}s   3段优化={ot:.1f}s   2段={kt:.1f}s")
