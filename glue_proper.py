"""正确的胶水模型: S, 公式数N, 阶段数k 都是变量, 用覆盖关系 N_i=V_i/B(S,d_i).
B(S,d): 覆盖球. d=该段case最短距离(实测: 早期块~4, 棱~7, 角/顶层~10).
  S<d  -> 胶水够不着, B=1, 公式=满V (无折扣)
  S>=d -> 胶水启动, B 随(S-d)指数涨, 公式暴跌
DP over (c,e); 每段选(dc,de); N=V/B; 求 Σ步最小, Σ公式≤2000. 扫不同S。
"""
from math import factorial as fac

def P(n,k):
    r=1
    for i in range(k): r*=(n-i)
    return r

def variety(c,e,dc,de):
    co=3**dc if dc else 1; eo=2**de if de else 1
    raw = P(8-c,dc)*co*P(12-e,de)*eo
    # 对称(~24)+约束(~12) 只在第一段整体除一次, 后面不除(否则12^k重复削减)
    if c==0 and e==0:
        return max(1, raw//288)
    return max(1, raw)

def chunk_L(c,e,dc,de):
    # 估计该段最优步长(标定自实测: 8角~8, 8角+3棱~13)
    phi=(c+e+dc+de)/20.0
    L = 0.9*(dc+de) + 3 + 5*phi
    if de>0 and dc==0: L -= 1.5    # 纯棱用M, 更短
    return L

def formulas(c,e,dc,de,S):
    # 实测覆盖关系: N(S) = 覆盖系数 / (≤S步的比例); 比例由该段步长分布定
    V=variety(c,e,dc,de)
    L=chunk_L(c,e,dc,de)
    frac=max(0.0, min(1.0, (S - L + 4)/8.0))   # L附近±4的分布内, ≤S的比例
    if frac<=0: return V                        # 完全够不着 -> 满公式
    return max(1.0, min(V, 3.0/frac))           # 3x = 贪心覆盖比下界高(实测~25@frac0.12)

def step_moves(c,e,dc,de,S):
    # 角~2/块(交换子); 棱用M, M算1.5步 -> 棱~1.5/块; 每段衔接开销3
    return dc*2.0 + de*1.5 + 3

def solve(S, budget=2000):
    best={}
    def go(c,e):
        if (c,e)==(8,12): return (0.0,0.0,[])
        if (c,e) in best: return best[(c,e)]
        best[(c,e)]=(1e9,0,[])
        bm=1e9;bf=0;bp=[]
        for dc in range(0, (8-c)+1):           # 放开块大小, 让阶段数自由
            for de in range(0, (12-e)+1):
                if dc==0 and de==0: continue
                mv=step_moves(c,e,dc,de,S)
                Ncov=formulas(c,e,dc,de,S)     # 覆盖小表+胶水
                V=variety(c,e,dc,de)           # 1-look满表(对称已在variety里整体除过)
                sub=go(c+dc,e+de)
                # 两种模式: 覆盖(base步) / 满表(base-2步, 但吃V条)
                for (Nuse, muse) in [(Ncov, mv), (min(V,99999), mv-2)]:
                    tm=muse+sub[0]; tf=Nuse+sub[1]
                    if tf<=budget and tm<bm:
                        bm,bf,bp=tm,tf,[(dc,de,Nuse)]+sub[2]
        best[(c,e)]=(bm,bf,bp); return best[(c,e)]
    return go(0,0)

if __name__=="__main__":
    print("正确胶水模型 (S/公式/阶段 都是变量): 扫不同 S\n")
    print(f"{'S':>3} {'阶段k':>5} {'总步':>6} {'总公式':>8}")
    print("-"*32)
    for S in (3,5,7,9,11,13):
        m,f,path=solve(S)
        print(f"{S:>3} {len(path):>5} {m:>6.0f} {f:>8.0f}")
    print("\n例: S=7 的里程碑链:")
    m,f,path=solve(7)
    c=e=0
    for dc,de,N in path:
        c+=dc;e+=de
        print(f"  +{dc}角{de}棱 (公式{N:.0f}条) -> 已解({c},{e})")
    print(f"  总: {m:.0f}步 / {f:.0f}公式 / {len(path)}阶段")
