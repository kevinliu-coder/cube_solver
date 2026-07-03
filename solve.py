"""命令行求解入口。

用法:
    python3 solve.py "R U R' U' F2 L D2 ..."     # 解一个打乱
    python3 solve.py                              # 不给参数则随机打乱一个

合法转动记号: U D L R F B,各自可加 2(180度) 或 '(逆时针)。
"""
import sys, random
from twophase import solve, verify
from tables import MOVE_NAMES

if len(sys.argv) > 1:
    scramble = sys.argv[1]
else:
    scramble = " ".join(random.choice(MOVE_NAMES) for _ in range(25))
    print(f"随机打乱: {scramble}\n")

sol, n = solve(scramble, timeout=10.0, verbose=True)
if sol is None:
    print("超时未找到解,试着调大 timeout")
else:
    print(f"\n解法 ({n} 步): {sol}")
    print(f"验证: {'✓ 还原成功' if verify(scramble, sol) else '✗ 错误'}")
