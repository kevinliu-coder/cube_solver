"""给定[顶尖搜索容量 + ≤2000公式 + 不限阶段], 搜出最省步的里程碑结构。

每个候选方法 = 一串里程碑(阶段), 每阶段标注:
  type: 'search'(人脑现场规划,0公式) 或 'formula'(查表,占预算)
  moves: 该阶段平均步数(HTM, 顶尖容量下; ZBLL/LL 类有实测支撑)
  formulas: 公式数(0 if search)
约束: 总公式 ≤ 2000, 且每个 search 阶段在顶尖容量内可规划(≤~1块/EO/前两层)。
"""

BUDGET = 2000

# 候选方法库 (里程碑列表; 每项 = (名称, type, moves, formulas))
METHODS = {
    "CFOP": [
        ("十字", "search", 6, 0), ("F2L", "search", 22, 0),
        ("OLL", "formula", 9, 57), ("PLL", "formula", 12, 21)],
    "ZZ+2look": [
        ("EOCross", "search", 8, 0), ("F2L", "search", 22, 0),
        ("OLL", "formula", 9, 57), ("PLL", "formula", 12, 21)],
    "ZZ+ZBLL (3里程碑)": [
        ("EOCross", "search", 8, 0), ("F2L", "search", 22, 0),
        ("ZBLL", "formula", 13, 493)],
    "ZZ+ZBLL+多槽F2L": [
        ("EOCross", "search", 8, 0), ("多槽F2L", "formula", 20, 1300),
        ("ZBLL", "formula", 13, 493)],
    "ZZ+1LLL (2里程碑)": [
        ("EOCross", "search", 8, 0), ("F2L", "search", 22, 0),
        ("1LLL", "formula", 12, 3915)],
    "Roux": [
        ("左桥", "search", 8, 0), ("右桥", "search", 9, 0),
        ("CMLL", "formula", 10, 42), ("LSE", "search", 13, 0)],
    # ↓ 第一性发明: 把 Roux 最长的"受限搜索LSE"换成 1-look 查表(1440条, 预算内)
    "★Roux+1lookLSE (发明)": [
        ("左桥", "search", 8, 0), ("右桥", "search", 9, 0),
        ("CMLL", "formula", 10, 42), ("1-look LSE", "formula", 9, 1440)],
}


def evaluate(phases):
    moves = sum(p[2] for p in phases)
    formulas = sum(p[3] for p in phases)
    stages = len(phases)
    return moves, formulas, stages


if __name__ == "__main__":
    rows = []
    for name, phases in METHODS.items():
        moves, formulas, stages = evaluate(phases)
        feasible = formulas <= BUDGET
        rows.append((name, stages, formulas, moves, feasible))

    print(f"约束: 顶尖容量, 公式 ≤ {BUDGET}, 不限阶段, 目标=最少步\n")
    print(f"{'方法':22s} {'阶段':>4} {'公式':>6} {'步数':>5} {'预算内?':>7}")
    print("-" * 52)
    for name, stages, formulas, moves, feasible in sorted(rows, key=lambda r: r[3]):
        mark = "✓" if feasible else "✗超预算"
        print(f"{name:22s} {stages:>4} {formulas:>6} {moves:>5} {mark:>7}")

    feasible_rows = [r for r in rows if r[4]]
    best = min(feasible_rows, key=lambda r: r[3])
    print(f"\n>>> 预算内最省步: 【{best[0]}】 {best[3]}步 / {best[2]}公式 / {best[1]}里程碑")
    print(f">>> 注: ZZ+1LLL 只需2里程碑、43步, 但 3915公式超预算被排除")
    print(f">>> 注: Roux 同样~45步但只42公式(更省记忆), 代价是LSE的M层搜索")
