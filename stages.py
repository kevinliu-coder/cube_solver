"""把 3 阶段方法每一段做完后的魔方样子用展开图画出来。"""
from cubie import CubieCube, MOVES, apply_sequence
from thistle3 import solve3, verify

# ---- cubie -> 54 facelet (Kociemba 标准映射) ----
cornerFacelet = [
    [8, 9, 20], [6, 18, 38], [0, 36, 47], [2, 45, 11],
    [29, 26, 15], [27, 44, 24], [33, 53, 42], [35, 17, 51],
]
cornerColor = [
    [0, 1, 2], [0, 2, 4], [0, 4, 5], [0, 5, 1],
    [3, 2, 1], [3, 4, 2], [3, 5, 4], [3, 1, 5],
]
edgeFacelet = [
    [5, 10], [7, 19], [3, 37], [1, 46], [32, 16], [28, 25],
    [30, 43], [34, 52], [23, 12], [21, 41], [50, 39], [48, 14],
]
edgeColor = [
    [0, 1], [0, 2], [0, 4], [0, 5], [3, 1], [3, 2],
    [3, 4], [3, 5], [2, 1], [2, 4], [5, 4], [5, 1],
]

EMOJI = ["⬜", "🟥", "🟩", "🟨", "🟧", "🟦"]  # U R F D L B


def to_facelets(c: CubieCube):
    f = [0] * 54
    for idx, face in zip([4, 13, 22, 31, 40, 49], range(6)):
        f[idx] = face
    for i in range(8):
        j, o = c.cp[i], c.co[i]
        for k in range(3):
            f[cornerFacelet[i][(k + o) % 3]] = cornerColor[j][k]
    for i in range(12):
        j, o = c.ep[i], c.eo[i]
        for k in range(2):
            f[edgeFacelet[i][(k + o) % 2]] = edgeColor[j][k]
    return f


def net(c: CubieCube) -> str:
    f = to_facelets(c)
    def row(face, r):
        return "".join(EMOJI[f[face * 9 + r * 3 + col]] for col in range(3))
    pad = "      "
    lines = []
    for r in range(3):
        lines.append(pad + row(0, r))
    for r in range(3):
        lines.append(row(4, r) + " " + row(2, r) + " " + row(1, r) + " " + row(5, r))
    for r in range(3):
        lines.append(pad + row(3, r))
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    scramble = sys.argv[1] if len(sys.argv) > 1 else \
        "R U2 F' L D2 B R' U F2 D L2 B2 U' R2 D F' R U2 L'"
    sol, total, br = solve3(scramble)
    assert verify(scramble, sol)
    moves = sol.split()
    s1, s2, s3 = moves[:br[0]], moves[br[0]:br[0] + br[1]], moves[br[0] + br[1]:]

    cube = apply_sequence(scramble)
    print(f"打乱: {scramble}\n")
    print("【打乱后】乱成一团:")
    print(net(cube))

    for m in s1:
        cube.multiply(MOVES[m])
    print(f"\n【阶段1 完成 · {len(s1)}步: {' '.join(s1)}】")
    print("  目标=12个棱块全部定向正确(能不靠 F/B 转动归位)。肉眼还很乱,但棱朝向已锁定:")
    print(net(cube))

    for m in s2:
        cube.multiply(MOVES[m])
    print(f"\n【阶段2 完成 · {len(s2)}步: {' '.join(s2)}】")
    print("  目标=8个角块全部定向(顶/底色朝上下)+4个中层棱回到中层。结构开始成形:")
    print(net(cube))

    for m in s3:
        cube.multiply(MOVES[m])
    print(f"\n【阶段3 完成 · {len(s3)}步: {' '.join(s3)}】")
    print("  目标=完全还原:")
    print(net(cube))

    print(f"\n总计 {total} 步 = {len(s1)} + {len(s2)} + {len(s3)}")
