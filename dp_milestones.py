"""胶水模型 完整枚举所有里程碑组合 (DP).
状态 = (已解角数c, 已解棱数e). 从(0,0)到(8,12).
每步加 (dc,de) 一小块, 成本一致地算:
  该步 variety V = 在剩余槽放这些新块的配置数
  搜索成本 = 步数(随"已解越多越纠缠"上升; 棱用M打折)
  公式成本 = N(S)=V/ball(S) 条, 步数较短
  每步取 min(搜索, 公式), 全程 Σ公式≤2000, 求总步最少。
ball(S): 用实测——早期块case近(ball大),晚期纠缠case远(ball小)。
"""
from math import factorial as fac

S = 7
def P(n,k):
    r=1
    for i in range(k): r*=(n-i)
    return r

def variety(c,e,dc,de):
    co = 3**dc if dc else 1
    eo = 2**de if de else 1
    return max(1, P(8-c,dc)*co * P(12-e,de)*eo // 6)

def ball(phi):
    # phi=已解比例. 早期(phi小)块近, 半径S盖很多; 晚期(phi大)纠缠, 盖很少
    # 实测: 顶层(phi~0.6)最短10步>S=7 -> ball~1; 早期块~能盖2000+
    import math
    reach = max(1.0, (S*1.0)**3 * (1.0 - phi)**3 * 30)   # 粗模型
    return reach

def search_moves(c,e,dc,de):
    phi=(c+e)/20
    cm = dc*(2+5*phi)              # 角: 越晚越贵(交换子)
    em = de*(2+5*phi)*0.6          # 棱: M打折
    return cm+em

def formula(c,e,dc,de):
    V=variety(c,e,dc,de)
    N=max(1, V/ball((c+e)/20))
    moves=(dc+de)*1.8 + 2          # 公式较短
    return N, moves

# DP: 对每个状态记录 (最小步, 用的公式, 路径)
from functools import lru_cache
import sys
sys.setrecursionlimit(10000)

best={}  # (c,e)->(moves, formulas, path)
def solve(c,e):
    if (c,e)==(8,12): return (0,0,[])
    if (c,e) in best: return best[(c,e)]
    best[(c,e)]=(1e9,0,[])  # 防环
    bm=1e9; bf=0; bp=[]
    for dc in range(0, min(2,8-c)+1):
        for de in range(0, min(3,12-e)+1):
            if dc==0 and de==0: continue
            sm=search_moves(c,e,dc,de)
            N,fm=formula(c,e,dc,de)
            # 选搜索还是公式(按步数, 公式占预算)
            if sm<=fm:
                use_m, use_f, tag = sm, 0, f'搜{dc}角{de}棱'
            else:
                use_m, use_f, tag = fm, N, f'公式{dc}角{de}棱({N:.0f}条)'
            sub=solve(c+dc, e+de)
            tot_m=use_m+sub[0]; tot_f=use_f+sub[1]
            if tot_f<=2000 and tot_m<bm:
                bm,bf,bp = tot_m, tot_f, [(tag,c+dc,e+de)]+sub[2]
    best[(c,e)]=(bm,bf,bp)
    return best[(c,e)]

if __name__=="__main__":
    m,f,path=solve(0,0)
    print(f"胶水DP 完整枚举(S={S}, 公式≤2000) 最优里程碑链:\n")
    print(f"总步数 ≈ {m:.0f}   总公式 ≈ {f:.0f}\n")
    print("里程碑路径(每步做法 -> 到达(角,棱)):")
    for tag,c,e in path:
        print(f"  {tag:24s} -> 已解({c}角,{e}棱)")
    print(f"\n注: 成本模型(搜索步/ball(S))是估算, 非全实测; 结构供参考。")
