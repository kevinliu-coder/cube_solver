"""自然的 S=(D,R) 模型, 方法无关。重做 (2000 + S_业余) 最优。

规则(无关任何具体方法):
  search 阶段: 总能做(若单段>D则拆成多个≤D小段, 仍可搜)。move=最优步数。
  formula 阶段: 仅当 表≤R 可用。
  全局: 总公式 ≤ 2000。
  -> 不再有"禁EO""禁块"这种特设排除。
"""
# 业余高手的自然容量
D = 9      # 规划深度: 一段能搜 ~9 步 (拆段后任意长phase都可搜)
R = 150    # 识别容量: 能认的公式表 ≤150 条

# 方法库: 阶段 = (名, type, moves, formulas)
METHODS = {
    "CFOP":          [("十字","s",6,0),("F2L","s",22,0),("OLL","f",9,57),("PLL","f",12,21)],
    "ZZ+2look":      [("EOCross","s",8,0),("F2L","s",22,0),("OLL","f",9,57),("PLL","f",12,21)],
    "ZZ+ZBLL":       [("EOCross","s",8,0),("F2L","s",22,0),("ZBLL","f",13,493)],
    "Roux":          [("左桥","s",7,0),("右桥","s",9,0),("CMLL","f",10,42),("LSE","s",13,0)],
    "Roux+1lookLSE": [("左桥","s",7,0),("右桥","s",9,0),("CMLL","f",10,42),("1lookLSE","f",9,1440)],
    "ZZ+1LLL":       [("EOCross","s",8,0),("F2L","s",22,0),("1LLL","f",12,3915)],
}


def valid(phases):
    total_f = sum(p[3] for p in phases)
    if total_f > 2000: return False, "超2000预算"
    for name, typ, mv, f in phases:
        if typ == "f" and f > R:
            return False, f"[{name}]表{f}>R={R}"
        # search 阶段: 自然模型下总可做(拆≤D段), 不排除
    return True, ""


if __name__ == "__main__":
    print(f"自然 S_业余: D={D}(规划深度), R={R}(识别上限), 预算2000")
    print("(search阶段一律合法=可拆段搜; 只有公式表受R限)\n")
    print(f"{'方法':16s} {'步数':>5} {'公式':>6} {'合法?':>6}  原因")
    print("-"*54)
    legal=[]
    for name, ph in METHODS.items():
        ok, why = valid(ph)
        mv=sum(p[2] for p in ph); f=sum(p[3] for p in ph)
        if ok: legal.append((name,mv,f)); why="✓"
        print(f"{name:16s} {mv:>5} {f:>6} {'✓' if ok else '✗':>6}  {why}")
    best=min(legal,key=lambda r:r[1])
    print(f"\n>>> 自然 S_业余 + 2000 下最优: 【{best[0]}】 {best[1]}步 / {best[2]}公式")
    print(f">>> Roux 不再被排除, 反而最省步。我上一版的 CFOP 结论是特设S的产物。")
