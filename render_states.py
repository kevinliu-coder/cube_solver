"""把候选解法的"里程碑状态"画成展开图(掩码版)。

🟨🟥🟩🟧🟦⬜ = 已锁定的块(位置+颜色固定)
⬛           = 还没锁定(自由)

底面取黄(D), 作为搭建基准。
"""

EMOJI = ["⬜", "🟥", "🟩", "🟨", "🟧", "🟦"]  # U R F D L B
GRAY = "⬛"

# 面: U(0) R(1) F(2) D(3) L(4) B(5), 每面9格 = face*9 + (row*3+col)
def fidx(face, r, c):
    return face * 9 + r * 3 + c


def net(mask):
    """mask: 已锁定的 facelet 索引集合。"""
    def cell(i):
        return EMOJI[i // 9] if i in mask else GRAY
    def row(face, r):
        return "".join(cell(face * 9 + r * 3 + c) for c in range(3))
    pad = "      "
    lines = []
    for r in range(3):
        lines.append(pad + row(0, r))
    for r in range(3):
        lines.append(row(4, r) + " " + row(2, r) + " " + row(1, r) + " " + row(5, r))
    for r in range(3):
        lines.append(pad + row(3, r))
    return "\n".join(lines)


# ---- 里程碑掩码 ----
D_FACE = set(range(27, 36))
# 底十字 = D中心+4棱 + 四侧底边中心
CROSS = {31, 28, 30, 32, 34, 25, 16, 52, 43}
# F2L = 整个底层 + 四侧下面两层
F2L = D_FACE | {21, 22, 23, 24, 25, 26} | {12, 13, 14, 15, 16, 17} \
      | {48, 49, 50, 51, 52, 53} | {39, 40, 41, 42, 43, 44}
# 顶层(剩下没解的) = 全集 - F2L
LAST_LAYER = set(range(54)) - F2L
SOLVED = set(range(54))

# Roux 右桥(右侧 1x2x3): D 右两列 + R 面整面 + F/B 右两列下两层 (近似)
RBLOCK = {fidx(3, r, c) for r in range(3) for c in (1, 2)} \
       | set(range(9, 18)) \
       | {fidx(2, r, 2) for r in (1, 2)} | {fidx(5, r, 0) for r in (1, 2)}
LBLOCK = {fidx(3, r, c) for r in range(3) for c in (0, 1)} \
       | set(range(36, 45)) \
       | {fidx(2, r, 0) for r in (1, 2)} | {fidx(5, r, 2) for r in (1, 2)}
BRIDGES = RBLOCK | LBLOCK


if __name__ == "__main__":
    print("=" * 32, "\n方法A · CFOP合并版 (十字→F2L→1LLL)\n")
    print("【状态1: 底十字】底面一个'+', 4棱位置颜色都对:")
    print(net(CROSS))
    print("\n【状态2: F2L 前两层】整个下半截锁死, 只剩顶层8块:")
    print(net(F2L))
    print("\n【状态3→还原: 1LLL一步收顶层】顶层这8块一张表搞定:")
    print(net(LAST_LAYER), "  ← 这坨(⬛)就是1LLL要一次收掉的")

    print("\n" + "=" * 32, "\n方法B · Roux合并版 (左右桥 → 顶角 → 后6棱)\n")
    print("【状态1: 左桥+右桥】左右各一个 1x2x3, 中层和顶自由 (你说的六色底左右桥):")
    print(net(BRIDGES))
