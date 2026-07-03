"""角块求解器: 一次解掉全部8个角(忽略棱). 实现 S=9 里程碑2 的核心。
IDA* on (角置换cperm, 角朝向twist) -> (0,0), 全18步.
"""
from cubie import CubieCube, MOVES, apply_sequence
import coord as C
from tables import MOVE_NAMES

# 角移动表(18步) + 剪枝
def build():
    NP, NT = C.N_CPERM, C.N_TWIST
    cpm=[[0]*18 for _ in range(NP)]
    twm=[[0]*18 for _ in range(NT)]
    for p in range(NP):
        base=CubieCube(); C.set_corner_perm(base,p)
        for mi,mn in enumerate(MOVE_NAMES):
            c=base.copy(); c.corner_multiply(MOVES[mn]); cpm[p][mi]=C.get_corner_perm(c)
    for t in range(NT):
        base=CubieCube(); C.set_twist(base,t)
        for mi,mn in enumerate(MOVE_NAMES):
            c=base.copy(); c.corner_multiply(MOVES[mn]); twm[t][mi]=C.get_twist(c)
    # BFS 剪枝
    def bfs(move,n,goal):
        d=bytearray([255])*n; d[goal]=0; fr=[goal]; dep=0
        while fr:
            nx=[]; dep+=1
            for s in fr:
                for mi in range(18):
                    ns=move[s][mi]
                    if d[ns]==255: d[ns]=dep; nx.append(ns)
            fr=nx
        return d
    return cpm,twm,bfs(cpm,NP,0),bfs(twm,NT,0)

CPM,TWM,PCP,PTW=build()

def solve_corners(scramble):
    cube=apply_sequence(scramble)
    cp=C.get_corner_perm(cube); tw=C.get_twist(cube)
    sol=[]
    def h(cp,tw): return max(PCP[cp],PTW[tw])
    def search(cp,tw,g,bound,last):
        f=g+h(cp,tw)
        if f>bound: return f
        if cp==0 and tw==0: return -1
        mn=99
        for mi in range(18):
            if last>=0 and mi//3==last//3: continue
            r=search(CPM[cp][mi],TWM[tw][mi],g+1,bound,mi)
            if r==-1: sol.append(MOVE_NAMES[mi]); return -1
            if r<mn: mn=r
        return mn
    bound=h(cp,tw)
    while True:
        sol.clear()
        r=search(cp,tw,0,bound,-1)
        if r==-1: sol.reverse(); return sol
        bound=r

if __name__=="__main__":
    scr='R U2 F D B2 L F2 R U D2 B R2 U F2 L2 D B2 R F'
    sol=solve_corners(scr)
    # 验证: 施加后8角全解
    c=apply_sequence(scr)
    for m in sol: c.multiply(MOVES[m])
    ok = (c.cp==list(range(8)) and c.co==[0]*8)
    print('打乱:', scr)
    print(f'\n一次解掉全部8个角 ({len(sol)}步):')
    print(' ', ' '.join(sol))
    msg = "全部归位+定向 OK" if ok else "失败"
    print(f'\n验证: 8个角 {msg} (棱还乱着, 留给后面阶段)')
