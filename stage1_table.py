"""S=5 阶段1 = 解 1角(DFR) + 2棱(DF,DB) 的公式表.
按正确流程: 每个'前置'(这3块的一种配置) -> 一条公式(到里程碑).
小坐标 IDA*, 浅搜, 快.
"""
from cubie import CubieCube, MOVES, apply_sequence
from tables import MOVE_NAMES

C4=4          # 角 DFR (home槽4)
E=[5,7]       # 棱 DF, DB (home槽5,7)

# ---- 角坐标: 角4在哪个槽(0-7)+朝向(0-2) = 24态 ----
def c_coord(cube):
    for s in range(8):
        if cube.cp[s]==C4: return s*3+cube.co[s]
def c_set(cube,cd):
    s,o=divmod(cd,3); cube.cp=[0,1,2,3,4,5,6,7]; cube.co=[0]*8
    # 把角4放到槽s(朝向o), 其余随便(不影响角4的转移)
    cube.cp[4],cube.cp[s]=cube.cp[s],cube.cp[4]
    cube.co[s]=o; return s
CM=[[0]*18 for _ in range(24)]
for cd in range(24):
    c=CubieCube(); c_set(c,cd)
    for mi,mn in enumerate(MOVE_NAMES):
        cc=c.copy(); cc.corner_multiply(MOVES[mn]); CM[cd][mi]=c_coord(cc)
GC=c_coord(CubieCube())
PC=bytearray([255])*24; PC[GC]=0; fr=[GC]; d=0
while fr:
    nx=[]; d+=1
    for s in fr:
        for mi in range(18):
            if PC[CM[s][mi]]==255: PC[CM[s][mi]]=d; nx.append(CM[s][mi])
    fr=nx

# ---- 棱坐标: 2棱(5,7)的(位置,朝向) ----
def e_coord(cube):
    p=[0,0]; o=[0,0]
    for s in range(12):
        if cube.ep[s]==5: p[0]=s; o[0]=cube.eo[s]
        if cube.ep[s]==7: p[1]=s; o[1]=cube.eo[s]
    return ((p[0]*12+p[1])*2+o[0])*2+o[1]
def e_set(cube,cd):
    cd,o1=divmod(cd,2); cd,o0=divmod(cd,2); p0,p1=divmod(cd,12)
    if p0==p1: return False
    cube.ep=list(range(12)); cube.eo=[0]*12
    ep=[-1]*12; ep[p0]=5; ep[p1]=7; eo=[0]*12; eo[p0]=o0; eo[p1]=o1
    others=[v for v in range(12) if v not in (5,7)]; k=0
    for s in range(12):
        if ep[s]==-1: ep[s]=others[k]; k+=1
    cube.ep=ep; cube.eo=eo; return True
NE=12*12*4
EM=[None]*NE
for cd in range(NE):
    c=CubieCube()
    if not e_set(c,cd): continue
    EM[cd]=[0]*18
    for mi,mn in enumerate(MOVE_NAMES):
        cc=c.copy(); cc.edge_multiply(MOVES[mn]); EM[cd][mi]=e_coord(cc)
GE=e_coord(CubieCube())
PE=bytearray([255])*NE; PE[GE]=0; fr=[GE]; d=0
while fr:
    nx=[]; d+=1
    for s in fr:
        if EM[s] is None: continue
        for mi in range(18):
            if PE[EM[s][mi]]==255: PE[EM[s][mi]]=d; nx.append(EM[s][mi])
    fr=nx

def solve(scr):
    cube=apply_sequence(scr); cc=c_coord(cube); ec=e_coord(cube); sol=[]
    def h(cc,ec): return max(PC[cc],PE[ec])
    def s(cc,ec,g,b,last):
        f=g+h(cc,ec)
        if f>b: return f
        if cc==GC and ec==GE: return -1
        mn=99
        for mi in range(18):
            if last>=0 and mi//3==last//3: continue
            r=s(CM[cc][mi],EM[ec][mi],g+1,b,mi)
            if r==-1: sol.append(MOVE_NAMES[mi]); return -1
            if r<mn: mn=r
        return mn
    b=h(cc,ec)
    while True:
        sol.clear()
        if s(cc,ec,0,b,-1)==-1: sol.reverse(); return sol
        b+=1

if __name__=="__main__":
    import random
    rng=random.Random(1)
    print("S=5 阶段1 公式表样例 (解 DFR角 + DF/DB棱):\n")
    print(f"{'前置(打乱后这3块的样子)':28s} -> {'公式(到里程碑1)'}")
    print("-"*60)
    for _ in range(10):
        scr=' '.join(rng.choice(MOVE_NAMES) for _ in range(12))
        alg=solve(scr)
        print(f"{scr[:26]:28s} -> {' '.join(alg)}")
