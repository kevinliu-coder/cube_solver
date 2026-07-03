"""「手法顺」的清晰定义 + 手感成本函数。

真实速度 ≈ 步数 / 手速; 手速由每步的执行难度和换握决定。
手感成本(ergo cost) = Σ 每步基础难度 + Σ 换握惩罚。
越低越顺; 纯 2-gen(只 R,U) 成本最低。
"""
from __future__ import annotations
import re

# ---- ① 每步基础难度 ----
BASE = {
    "U": 1.0, "R": 1.0,            # 最快: 弹指
    "F": 1.8,                      # 略调握
    "L": 2.2, "D": 2.2,            # 弱手/底面
    "B": 3.0,                      # 最别扭
    "x": 2.5, "y": 2.5, "z": 2.5,  # 整手换握(转体)
    "M": 2.3, "E": 2.6, "S": 2.6,  # 中层滑层
}
# 宽层 Rw/Lw... 介于面与转体之间
WIDE_EXTRA = 0.6
DOUBLE_EXTRA = 0.3   # x2 比 x 多一下

# ---- ② 换握档位 ----  A=快(R,U)  B=中(F,L)  C=慢(D,B)  X=转体/滑层
GRIP = {"U": "A", "R": "A", "F": "B", "L": "B", "D": "C", "B": "C",
        "x": "X", "y": "X", "z": "X", "M": "X", "E": "X", "S": "X"}
REGRIP = {
    ("A", "A"): 0.0, ("A", "B"): 0.8, ("A", "C"): 1.6, ("A", "X"): 1.8,
    ("B", "A"): 0.8, ("B", "B"): 0.3, ("B", "C"): 1.4, ("B", "X"): 1.6,
    ("C", "A"): 1.6, ("C", "B"): 1.4, ("C", "C"): 0.6, ("C", "X"): 1.6,
    ("X", "A"): 1.8, ("X", "B"): 1.6, ("X", "C"): 1.6, ("X", "X"): 0.8,
}


def _base_face(tok: str) -> str:
    """取转动的"面字母"(去掉 w ' 2 和大小写)。"""
    m = re.match(r"([URFDLBxyzMES])", tok)
    return m.group(1) if m else "U"


def move_cost(tok: str) -> float:
    f = _base_face(tok)
    c = BASE.get(f, 2.0)
    if "w" in tok or tok[:1].islower() and f in "urfdlb":  # 宽层
        c += WIDE_EXTRA
    if tok.endswith("2"):
        c += DOUBLE_EXTRA
    return c


def ergo_cost(alg) -> float:
    toks = alg.split() if isinstance(alg, str) else list(alg)
    total, prev = 0.0, None
    for t in toks:
        total += move_cost(t)
        if prev is not None:
            total += REGRIP[(GRIP[_base_face(prev)], GRIP[_base_face(t)])]
        prev = t
    return round(total, 2)


def htm(alg) -> int:
    """半转度量步数(把转体不计步,与社区习惯一致)。"""
    toks = alg.split() if isinstance(alg, str) else list(alg)
    return sum(1 for t in toks if _base_face(t) in "URFDLBMES")


def is_2gen(alg) -> bool:
    toks = alg.split() if isinstance(alg, str) else list(alg)
    return all(_base_face(t) in "RU" for t in toks)


if __name__ == "__main__":
    # 用真实公式验证: 顺度排序应符合手感直觉
    cases = [
        ("Sexy move",      "R U R' U'"),
        ("Ua-perm (2-gen)", "R U' R U R U R U' R' U' R2"),
        ("H-perm (2gen+M)", "M2 U M2 U2 M2 U M2"),
        ("T-perm (RUF)",   "R U R' U' R' F R2 U' R' U' R U R' F'"),
        ("Y-perm (RUF+rot)", "F R U' R' U' R U R' F' R U R' U' R' F R F'"),
        ("E-perm (rot+D)", "x' R U' R' D R U R' D' R U R' D R U' R' D' x"),
    ]
    print(f"{'公式':22s} {'步数':>4} {'手感成本':>8} {'2-gen':>6}")
    rows = []
    for name, alg in cases:
        e = ergo_cost(alg); h = htm(alg)
        rows.append((name, alg, h, e))
        print(f"{name:22s} {h:>4} {e:>8.1f} {'是' if is_2gen(alg) else '':>6}")

    print("\n按手感成本排序(越顺越靠前):")
    for name, alg, h, e in sorted(rows, key=lambda r: r[3]):
        print(f"  {e:6.1f}  {name}  ({h}步)")

    # 同一个 case 不同公式: 步数多但更顺, 可能更快
    print("\n演示: 步数 ≠ 顺度")
    a = "R U R' U' R' F R2 U' R' U' R U R' F'"   # T-perm RUF, 14步
    b = "R U R' U R U2 R' U R U' R' U' R' F R F'" # 假想更长但更RU
    print(f"  A: {htm(a)}步 手感{ergo_cost(a):.1f}")
    print(f"  B: {htm(b)}步 手感{ergo_cost(b):.1f}")
