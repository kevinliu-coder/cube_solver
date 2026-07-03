"""统一程序: 枚举里程碑链 + S约束 + 每段覆盖码实测(有界BFS) + DP求最少步.
覆盖码 N(S) = 该段变体数 / 半径-S球(实测: 从还原态有界BFS到深度S, 数能到的状态).
S球内的算"胶水够得着"; 球外的要1张公式. N = 变体 / 球大小.
"""
from cubie import CubieCube, MOVES
from tables import MOVE_NAMES
from math import factorial as fac

def P(n,k):
    r=1
    for i in range(k): r*=(n-i)
    return r

# ---- 追踪 (角值集合, 棱值集合) 的状态: 各自(位置,朝向) ----
def state_key(cube, cvals, evals):
    cs=tuple((cube.cp.index(v) if v in cube.cp else -1, cube.co[cube.cp.index(v)]) for v in cvals)
    es=tuple((cube.ep.index(v), cube.eo[cube.ep.index(v)]) for v in evals)
    return (cs,es)

def ball_size(cvals, evals, S):
    """从还原态有界BFS到深度S, 数能到达的(这些块的)不同状态."""
    start=state_key(CubieCube(), cvals, evals)
    seen={start}; frontier=[CubieCube()]; depth=0
    while frontier and depth<S:
        depth+=1; nxt=[]
        for cube in frontier:
            for mn in MOVE_NAMES:
                cc=cube.copy(); cc.multiply(MOVES[mn])
                k=state_key(cc,cvals,evals)
                if k not in seen:
                    seen.add(k); nxt.append(cc)
        frontier=nxt
    return len(seen)

def variety(cvals, evals):
    c=len(cvals); e=len(evals)
    co=3**c if c else 1; eo=2**e if e else 1
    return P(8, c)*co * P(12, e)*eo // (288 if (c+e)>=1 else 1)  # 整体对称一次

# 选哪些具体块(自底向上): 角顺序, 棱顺序
CORD=[5,6,4,7,1,0,2,3]; EORD=[5,7,6,4,9,8,11,10,1,3,2,0]

def cover_N(c,e,dc,de,S):
    """里程碑(c,e)->(c+dc,e+de): 测新增块的覆盖码."""
    cvals=CORD[c:c+dc]; evals=EORD[e:e+de]
    if not cvals and not evals: return 0
    V=variety(cvals,evals)
    B=ball_size(cvals,evals,S)
    return max(1, V//B)

if __name__=="__main__":
    import sys
    S=int(sys.argv[1]) if len(sys.argv)>1 else 9
    print(f"实测各小段的覆盖码 N(S={S}) (有界BFS):\n")
    for (dc,de) in [(1,0),(0,1),(2,0),(0,2),(3,0),(0,3),(4,0),(2,1),(1,2),(3,1)]:
        N=cover_N(0,0,dc,de,S)
        V=variety(CORD[:dc],EORD[:de]); B=ball_size(CORD[:dc],EORD[:de],S)
        print(f"  {dc}角{de}棱: 变体{V:>8} / 球{B:>8} = N(S={S}) {N:>6}条", flush=True)
