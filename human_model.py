"""带"人脑搜索容量"约束的 3 阶段方法模型。

核心思想(本对话最终模型):
  方法 = 搜索阶段(人脑现场规划,0公式,但受搜索容量限制)
        + 公式阶段(查表,占公式预算,但受识别容量限制)
  搜索容量 = 一个阶段能规划多少块/多少步(随技能升高)
  识别容量 = 能可靠认多大的公式表(随技能升高)

各阶段步数(HTM): cross/EO 来自常识标定, ZBLL=14.8 为本仓库实测。
"""

# 各阶段平均步数(HTM) —— 搜索阶段=现场规划, 公式阶段=查表
MOVES = {
    "cross": 6, "eocross": 8,       # 搜索: 底十字 / 带EO的十字
    "f2l": 24,                       # 搜索: 前两层(配对现搭)
    "zbll": 13,                      # 公式: 一步收顶层(实测~14.8, 人类顺手~13), 493条
    "1lll": 12,                      # 公式: 无EO一步收, 3915条
    "oll": 9, "pll": 12,             # 公式: 2-look 收顶层, 57+21
}

# 技能档: 搜索容量(能否规划EO/多块) + 识别容量(能认多大表)
TIERS = [
    dict(name="顶尖 (sub-8)",   plan_eo=True,  recog=600,  desc="EO+前两层全程规划, 认全493 ZBLL, 色彩中立"),
    dict(name="高级 (sub-12)",  plan_eo=True,  recog=120,  desc="能搜F2L, EO勉强, 顶层只能2-look或部分ZBLL"),
    dict(name="业余高手 (sub-20)", plan_eo=False, recog=80, desc="能搜F2L配对, 不会EO规划, 顶层2-look"),
]


def best_method(tier):
    """给定技能档, 选出该档可行且最省步的方法。"""
    # 顶层收法: 容量够+会EO -> ZBLL(1段493); 否则 -> 2-look(2段78)
    if tier["plan_eo"] and tier["recog"] >= 493:
        ll = ("ZBLL", ["zbll"], 493, 1)
        first = ["eocross", "f2l"]            # 需要EO -> EOCross
    elif tier["recog"] >= 78:
        ll = ("OLL+PLL", ["oll", "pll"], 78, 2)
        first = ["cross", "f2l"]
    else:
        ll = ("OLL+PLL", ["oll", "pll"], 78, 2)
        first = ["cross", "f2l"]
    phases = first + ll[1]
    stages = len(first) + ll[3]
    moves = sum(MOVES[p] for p in phases)
    formulas = ll[2]
    return phases, stages, moves, formulas, ll[0]


if __name__ == "__main__":
    print(f"{'技能档':18s} {'方法':22s} {'里程碑':>5} {'公式':>6} {'步数HTM':>7}")
    print("-" * 66)
    for t in TIERS:
        phases, stages, moves, formulas, llname = best_method(t)
        method = "EOCross/F2L/" + llname if "eocross" in phases else "Cross/F2L/" + llname
        print(f"{t['name']:18s} {method:22s} {stages:>5} {formulas:>6} {moves:>7}")
    print()
    print("解读:")
    print("  顶尖: 搜索容量足 -> 能压成 3 阶段 + 一步ZBLL -> 最省步(~44)")
    print("  容量下降 -> EO规划做不了/ZBLL认不全 -> 退回 4 阶段 + 2-look -> 步数涨(~51)")
    print("  ===> 3阶段省下的步数, 是'搜索容量'解锁的, 不是'公式'买来的")
