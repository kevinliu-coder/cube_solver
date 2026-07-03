"""枚举顶层(LL)的 case 数 —— 即"要背多少条公式"。

前两层已还原。顶层 = U 层 4 角 + 4 棱。
可达状态: 角扭向和≡0(mod3), 棱翻向和≡0(mod2), 角置换与棱置换同奇偶。
  27 (角向) × 8 (棱向) × 24×24/2 (同奇偶置换) = 62,208 个可达顶层状态。

一个"子步骤"负责把某些特征归位; 它的公式数 = 该特征在 AUF(顶层预转) 下的等价类数。
AUF = 解前可先转 U 对齐, 等于把状态绕 U 轴旋转 0/1/2/3 次取规范形。
"""
from itertools import permutations, product
from cubie import CubieCube, MOVES


def parity(perm):
    p = list(perm); n = len(p); par = 0
    for i in range(n):
        for j in range(i + 1, n):
            if p[i] > p[j]:
                par ^= 1
    return par


def all_ll_states():
    """生成所有可达顶层 CubieCube(只动 U 层 4 角 4 棱)。"""
    corner_oris = [o for o in product(range(3), repeat=4) if sum(o) % 3 == 0]
    edge_oris = [o for o in product(range(2), repeat=4) if sum(o) % 2 == 0]
    perms = list(permutations(range(4)))
    for co in corner_oris:
        for eo in edge_oris:
            for cp in perms:
                for ep in perms:
                    if parity(cp) != parity(ep):
                        continue
                    c = CubieCube()
                    c.cp[0:4] = list(cp)
                    c.co[0:4] = list(co)
                    c.ep[0:4] = list(ep)
                    c.eo[0:4] = list(eo)
                    yield c


# 预转 U^0..U^3
_UPOW = [CubieCube()]
for _ in range(3):
    nxt = _UPOW[-1].copy(); nxt.multiply(MOVES["U"]); _UPOW.append(nxt)


def _auf_variants(c):
    """AUF 等价 = 前后各可绕 U 轴转: U^a · c · U^b, 共 16 种。"""
    for a in range(4):
        for b in range(4):
            t = _UPOW[a].copy()
            t.multiply(c)
            t.multiply(_UPOW[b])
            yield t


def count_cases(scope):
    """scope: 含 'cp','co','ep','eo' 的集合, 表示该子步关心哪些特征。
    返回 AUF(前后双侧) 等价类数(含已解状态)。"""
    seen = set()
    for c in all_ll_states():
        best = None
        for r in _auf_variants(c):
            feat = []
            if "cp" in scope: feat += list(r.cp[0:4])
            if "co" in scope: feat += list(r.co[0:4])
            if "ep" in scope: feat += list(r.ep[0:4])
            if "eo" in scope: feat += list(r.eo[0:4])
            t = tuple(feat)
            if best is None or t < best:
                best = t
        seen.add(best)
    return len(seen)


if __name__ == "__main__":
    print("枚举顶层 case 数 (= 公式数, 含已解1种)...\n")
    items = [
        ("1LLL  一步收顶层(全部)", {"cp", "co", "ep", "eo"}),
        ("OLL   定向全部(角向+棱向)", {"co", "eo"}),
        ("PLL   置换全部(角位+棱位)", {"cp", "ep"}),
        ("CO    只定向角", {"co"}),
        ("EO    只定向棱", {"eo"}),
        ("CPLL  只置换角", {"cp"}),
        ("EPLL  只置换棱", {"ep"}),
        ("COLL  角定向+角置换", {"co", "cp"}),
        ("ELL   棱定向+棱置换", {"eo", "ep"}),
    ]
    res = {}
    for name, scope in items:
        n = count_cases(scope)
        res[name[:4].strip()] = n
        print(f"  {name:28s} {n:6d}")
    print("\n校验: OLL 应=57, PLL 应=21, EPLL 应=5(含已解) — 对上说明枚举正确")
