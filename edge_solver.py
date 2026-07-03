"""
Edge solver v3: twophase full edge solve, split at U-flip-clear point.
Also finds the optimal M/U-only U-flip-clear for comparison.
"""
from cubie import CubieCube, MOVES, apply_sequence
from tables import MOVE_NAMES
from twophase import solve_cube
from collections import deque
import sys

# === M moves for corner-safe 凑 ===
def _define_moves():
    m_cube = CubieCube()
    m_cube.ep = list(range(12))
    m_cube.ep[0]=2; m_cube.ep[2]=6; m_cube.ep[6]=4; m_cube.ep[4]=0
    m_cube.eo=[0]*12; m_cube.eo[0]=m_cube.eo[2]=m_cube.eo[4]=m_cube.eo[6]=1
    mp=CubieCube()
    for _ in range(3): mp.multiply(m_cube)
    m2=CubieCube()
    for _ in range(2): m2.multiply(m_cube)
    MOVES['M']=m_cube; MOVES["M'"]=mp; MOVES['M2']=m2
_define_moves()

CUO_MOVES = ['U',"U'",'U2','M',"M'",'M2']

def corners_ok(c): return all(c.cp[i]==i and c.co[i]==0 for i in range(8))
def u_flip_clear(c): return all(c.eo[i]==0 for i in range(4))

def find_mu_cuo(cube, max_depth=8):
    """Find shortest M/U path to U-flip-clear. Returns moves list or None."""
    start_ep=tuple(cube.ep); start_eo=tuple(cube.eo)
    start=(start_ep, start_eo)
    q=deque([(start,[])])
    visited={start}
    while q:
        (ep,eo),path=q.popleft()
        if all(eo[i]==0 for i in range(4)):
            c=cube.copy()
            for m in path: c.multiply(MOVES[m])
            if corners_ok(c): return path
        if len(path)>=max_depth: continue
        c=CubieCube(); c.ep,c.eo=list(ep),list(eo)
        c.cp,c.co=list(cube.cp),list(cube.co)
        for m in CUO_MOVES:
            c2=c.copy(); c2.multiply(MOVES[m])
            st=(tuple(c2.ep),tuple(c2.eo))
            if st not in visited:
                visited.add(st)
                q.append((st,path+[m]))
    return None


def solve_edges(cube):
    """Full edge solve via twophase, split at U-flip-clear point.
    Returns (cuo_moves, formula_moves)."""
    assert corners_ok(cube)
    sol_e, n = solve_cube(cube, max_total=25, timeout=5.0)
    if sol_e is None: return None, None
    
    moves = sol_e.split()
    c = cube.copy()
    cuo_end = -1
    for i, m in enumerate(moves):
        c.multiply(MOVES[m])
        if all(c.eo[j]==0 for j in range(4)):
            cuo_end = i; break
    
    if cuo_end < 0:
        s = min(len(moves)//2, 8)
        return moves[:s], moves[s:]
    return moves[:cuo_end+1], moves[cuo_end+1:]


if __name__ == '__main__':
    from corner_solve import CPM, TWM, PCP, PTW
    import coord as C
    
    scr = sys.argv[1] if len(sys.argv) > 1 else \
        "B R B U R' L' F L D L U' D U' L' R' B' U' D F R' L' U' B D R'"
    
    print(f"打乱: {scr}\n")
    cube = apply_sequence(scr)
    
    # Corner solve
    cp=C.get_corner_perm(cube); tw=C.get_twist(cube)
    sol_c=[]
    def h(cp,tw): return max(PCP[cp],PTW[tw])
    def s(cp,tw,g,bd,last):
        f=g+h(cp,tw)
        if f>bd: return f
        if cp==0 and tw==0: return -1
        mn=99
        for mi in range(18):
            if last>=0 and mi//3==last//3: continue
            r=s(CPM[cp][mi],TWM[tw][mi],g+1,bd,mi)
            if r==-1: sol_c.append(MOVE_NAMES[mi]); return -1
            if r<mn: mn=r
        return mn
    bd=h(cp,tw)
    while True:
        sol_c.clear()
        if s(cp,tw,0,bd,-1)==-1: sol_c.reverse(); break
        bd+=1
    for m in sol_c: cube.multiply(MOVES[m])
    
    print(f"① 二阶角解 ({len(sol_c)}步): {' '.join(sol_c)}")
    print(f"   → 8角全解 ✓\n")
    
    # Find M/U 凑
    mu_cuo = find_mu_cuo(cube)
    print(f"M/U清棱 (纯M/U,不动角):")
    if mu_cuo:
        print(f"  最短{len(mu_cuo)}步: {' '.join(mu_cuo)}")
        c_mu = cube.copy()
        for m in mu_cuo: c_mu.multiply(MOVES[m])
        mu_uf = u_flip_clear(c_mu)
        mu_cok = corners_ok(c_mu)
        print(f"  → U翻棱{'✓' if mu_uf else '✗'} | 角全对{'✓' if mu_cok else '✗'}")
        if mu_uf and mu_cok:
            print(f"  → 此时U面四条棱只剩白/黄,角纹丝不动。这就是清棱完成的状态。")
    else:
        print(f"  8步内未找到")
    
    # Full solve with twophase
    cuo, formula = solve_edges(cube)
    c2 = cube.copy()
    for m in cuo: c2.multiply(MOVES[m])
    
    print(f"\n② 凑到清棱 ({len(cuo)}步): {' '.join(cuo)}")
    print(f"   → U翻棱: {'✓' if u_flip_clear(c2) else '✗'}")
    
    for m in formula: c2.multiply(MOVES[m])
    print(f"③ 公式收尾 ({len(formula)}步): {' '.join(formula)}")
    print(f"   → 完全还原: {'✓' if c2.is_solved() else '✗'}")
    
    print(f"\n总步数: {len(sol_c) + len(cuo) + len(formula)}")
    print(f"\n实操提示: ②用M/U替代(F/R/L/B会打乱角)。")
    print(f"  M/U清棱就是{' '.join(mu_cuo) if mu_cuo else '需手调'}，做完角不变。")
    print(f"  然后接③公式收尾即可。")
