"""实测各末尾块集 U 的"一步收"真实步数(HTM)。
构造: 只打乱 U 里的角/棱(其余还原), 求解, 取平均。这就是把 U 当公式收的步数。
"""
import random
from cubie import CubieCube, MOVES
from twophase import solve_cube
from tables import load
load()

def parity(p):
    par=0
    for i in range(len(p)):
        for j in range(i+1,len(p)):
            if p[i]>p[j]: par^=1
    return par

def rand_U_state(corner_slots, edge_slots, rng):
    """只打乱给定角槽/棱槽, 其余还原。返回合法 CubieCube。"""
    c=len(corner_slots); e=len(edge_slots)
    while True:
        # 角置换(在自己槽内) + 朝向
        cperm=corner_slots[:]; rng.shuffle(cperm)
        eperm=edge_slots[:];   rng.shuffle(eperm)
        pc = parity([corner_slots.index(x) for x in cperm]) if c>1 else 0
        pe = parity([edge_slots.index(x) for x in eperm]) if e>1 else 0
        if pc != pe: continue          # 总置换须偶
        co=[rng.randrange(3) for _ in range(c)]
        if c>0 and sum(co)%3: continue
        eo=[rng.randrange(2) for _ in range(e)]
        if e>0 and sum(eo)%2: continue
        cube=CubieCube()
        for i,slot in enumerate(corner_slots):
            cube.cp[slot]=cperm[i]; cube.co[slot]=co[i]
        for i,slot in enumerate(edge_slots):
            cube.ep[slot]=eperm[i]; cube.eo[slot]=eo[i]
        return cube

CANDS = [
    ("5棱",            [], [0,1,2,3,4]),
    ("6棱",            [], [0,1,2,3,4,5]),
    ("4角",            [0,1,2,3], []),
    ("2角+5棱",        [0,1], [0,1,2,3,4]),
    ("1角+5棱",        [0], [0,1,2,3,4]),
    ("4角+4棱(顶层)",  [0,1,2,3], [0,1,2,3]),
]

if __name__ == "__main__":
    rng=random.Random(33)
    print(f"{'末尾块集U':>14} {'块数':>4} {'实测一步收(HTM)':>14}")
    print("-"*40)
    for name, cs, es in CANDS:
        lens=[]
        for _ in range(25):
            cube=rand_U_state(cs, es, rng)
            sol,k=solve_cube(cube.copy(), max_total=22, timeout=2.0)
            cc=cube.copy()
            for m in sol.split(): cc.multiply(MOVES[m])
            assert cc.is_solved()
            lens.append(k)
        print(f"{name:>14} {len(cs)+len(es):>4} {sum(lens)/len(lens):>14.1f}")
