"""部分目标求解器: 从打乱解"8角 + 指定3棱"子目标(其余9棱自由).
= S=9 阶段2 的真实最优步长 -> 覆盖码 -> 公式数.
正确约束: 只要那3棱+8角到位, 别的棱随便(留给阶段3).
"""
from corner_solve import CPM, TWM, PCP, PTW
from cubie import CubieCube, MOVES, apply_sequence
import coord as C
from tables import MOVE_NAMES

TRACK = [5, 7, 6]   # 3条棱: DF DB DL (cubie值)
SOLVED_E3 = None

def e3_coord(cube):
    pos=[0,0,0]; ori=[0,0,0]
    for slot in range(12):
        v=cube.ep[slot]
        if v in TRACK:
            i=TRACK.index(v); pos[i]=slot; ori[i]=cube.eo[slot]
    pi=pos[0]*144+pos[1]*12+pos[2]
    oi=ori[0]*4+ori[1]*2+ori[2]
    return pi*8+oi

def e3_set(cube,coord):
    pi,oi=divmod(coord,8)
    p=[pi//144,(pi//12)%12,pi%12]
    o=[oi//4,(oi//2)%2,oi%2]
    if len(set(p))<3: return False
    ep=[-1]*12; eo=[0]*12
    for i in range(3): ep[p[i]]=TRACK[i]; eo[p[i]]=o[i]
    others=[v for v in range(12) if v not in TRACK]; k=0
    for s in range(12):
        if ep[s]==-1: ep[s]=others[k]; k+=1
    cube.ep=ep; cube.eo=eo; return True

print("building 3-edge tables...")
SOLVED_E3=e3_coord(CubieCube())
NE3=13824
E3M=[None]*NE3
for cd in range(NE3):
    c=CubieCube()
    if not e3_set(c,cd): continue
    row=[0]*18
    for mi,mn in enumerate(MOVE_NAMES):
        cc=c.copy(); cc.edge_multiply(MOVES[mn]); row[mi]=e3_coord(cc)
    E3M[cd]=row
# BFS prune
PE3=bytearray([255])*NE3
PE3[SOLVED_E3]=0; fr=[SOLVED_E3]; dep=0
while fr:
    nx=[]; dep+=1
    for s in fr:
        if E3M[s] is None: continue
        for mi in range(18):
            ns=E3M[s][mi]
            if PE3[ns]==255: PE3[ns]=dep; nx.append(ns)
    fr=nx
print("  done")

def solve_partial(scramble):
    cube=apply_sequence(scramble)
    cp=C.get_corner_perm(cube); tw=C.get_twist(cube); e3=e3_coord(cube)
    sol=[]
    def h(cp,tw,e3): return max(PCP[cp],PTW[tw],PE3[e3])
    def search(cp,tw,e3,g,bound,last):
        f=g+h(cp,tw,e3)
        if f>bound: return f
        if cp==0 and tw==0 and e3==SOLVED_E3: return -1
        mn=99
        for mi in range(18):
            if last>=0 and mi//3==last//3: continue
            r=search(CPM[cp][mi],TWM[tw][mi],E3M[e3][mi],g+1,bound,mi)
            if r==-1: sol.append(mi); return -1
            if r<mn: mn=r
        return mn
    b=h(cp,tw,e3)
    while True:
        sol.clear()
        if search(cp,tw,e3,0,b,-1)==-1:
            sol.reverse(); return [MOVE_NAMES[m] for m in sol]
        b+=1

def coverable(scramble, maxd):
    """≤maxd步能否解到'8角+3棱'? (有界, 快). 用于覆盖码."""
    cube=apply_sequence(scramble)
    cp=C.get_corner_perm(cube); tw=C.get_twist(cube); e3=e3_coord(cube)
    def h(cp,tw,e3): return max(PCP[cp],PTW[tw],PE3[e3])
    def dfs(cp,tw,e3,g,last):
        if cp==0 and tw==0 and e3==SOLVED_E3: return True
        if g+h(cp,tw,e3)>maxd: return False
        for mi in range(18):
            if last>=0 and mi//3==last//3: continue
            if dfs(CPM[cp][mi],TWM[tw][mi],E3M[e3][mi],g+1,mi): return True
        return False
    return dfs(cp,tw,e3,0,-1)

if __name__=="__main__":
    import random,sys
    rng=random.Random(3)
    N=80; cov=0
    for n in range(N):
        scr=' '.join(rng.choice(MOVE_NAMES) for _ in range(20))
        if coverable(scr,9): cov+=1
        if (n+1)%20==0: print(f"  跑了{n+1}/{N}, ≤9步覆盖 {cov}", flush=True)
    frac=cov/N
    print(f"\n8角+3棱: {N}个打乱中 {cov} 个能 ≤9步解到 ({frac*100:.0f}%)")
    print(f"S=9 阶段2 覆盖码 N(S=9) = 1/{frac:.2f} = {1/frac if frac else 9999:.0f} 条")
    print("(电脑侧实测: 这是'电脑能搜≤9步'的覆盖数, 不是人类识别数)")
    import statistics as st
    print(f"\n解 8角+3棱(其余9棱自由) 最优步长: 平均{st.mean(lens):.1f}, 范围{min(lens)}-{max(lens)}")
    print("覆盖码 N(S)=1/球内比例 (S=9阶段2真实公式数):")
    for S in (7,9,11,13):
        frac=sum(1 for L in lens if L<=S)/len(lens)
        N=(1/frac) if frac>0 else 99999
        print(f"  S={S}: 球内{frac*100:.0f}% -> N(S)={N:.0f}")
    print("\n对比: glue_proper模型给652")
