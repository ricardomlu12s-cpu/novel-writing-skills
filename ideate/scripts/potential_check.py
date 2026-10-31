#!/usr/bin/env python3
"""势能引擎检查 — 情节段四拍(欲望→障碍→蓄势→释放)是否齐、势能差够不够。

情节平淡 = 势能差不够。本脚本做确定性四拍检查(有/无 + 强度),标出缺哪一拍。

用法:
  python3 potential_check.py <章节文件.md>

输出: 四拍各打了多少分(0-5),缺哪一拍,势能差是否够。
"""
import re
import sys
from pathlib import Path

# 四拍信号词(确定性检测,不是语义理解)
DESIRE_WORDS = ["想要", "渴望", "一定要", "非要", "必须", "誓要", "无论如何", "拼了", "豁出去"]
OBSTACLE_WORDS = ["但是", "然而", "可是", "却", "偏", "挡", "阻止", "阻拦", "不许", "无法", "办不到", "陷阱", "封锁", "追杀"]
BUILDUP_WORDS = ["蓄", "积累", "压抑", "隐忍", "蛰伏", "等待", "按兵不动", "憋", "克制", "积蓄"]
RELEASE_WORDS = ["爆发", "出手", "出手了", "反击", "反击了", "摊牌", "揭晓", "反转", "一击", "咆哮", "宣泄", "爆发了"]

# 强度词(增强势能差)
INTENSITY_WORDS = ["血", "死", "杀", "恨", "怒", "毁", "灭", "崩", "绝", "疯", "狂", "誓"]


def count_words(text, words):
    return sum(text.count(w) for w in words)


def score(count, intensity_bonus):
    """count 命中数 + 强度词加权,映射到 0-5。"""
    raw = count + intensity_bonus
    if raw <= 0:
        return 0
    if raw <= 1:
        return 1
    if raw <= 3:
        return 2
    if raw <= 6:
        return 3
    if raw <= 10:
        return 4
    return 5


def main():
    if len(sys.argv) < 2:
        print("用法: potential_check.py <章节文件.md>")
        sys.exit(2)
    f = Path(sys.argv[1])
    if not f.exists():
        print(f"文件不存在: {f}")
        sys.exit(1)
    text = f.read_text(encoding="utf-8")

    intensity = count_words(text, INTENSITY_WORDS)
    intensity_bonus = min(2, intensity // 3)  # 强度词每 3 个 +1

    d = count_words(text, DESIRE_WORDS)
    o = count_words(text, OBSTACLE_WORDS)
    b = count_words(text, BUILDUP_WORDS)
    r = count_words(text, RELEASE_WORDS)

    sd, so, sb, sr = score(d, 0), score(o, 0), score(b, 0), score(r, intensity_bonus)

    print(f"势能引擎检查 @ {f.name}\n" + "=" * 60)
    print(f"  欲望(想要什么)  : {'█' * sd}{'·' * (5 - sd)}  {sd}/5  ({d} 处)")
    print(f"  障碍(什么挡住)  : {'█' * so}{'·' * (5 - so)}  {so}/5  ({o} 处)")
    print(f"  蓄势(张力积累)  : {'█' * sb}{'·' * (5 - sb)}  {sb}/5  ({b} 处)")
    print(f"  释放(爆发/反转) : {'█' * sr}{'·' * (5 - sr)}  {sr}/5  ({r} 处)")
    print(f"  强度词(血/死/恨): {intensity} 处 (+{intensity_bonus} 势能)")

    # 势能差 = 欲望 × 障碍 × 蓄势(释放是势能差的结果)
    potential = sd * so * sb
    print(f"\n  势能差 = 欲望{sd} × 障碍{so} × 蓄势{sb} = {potential} (满 125)")

    # 诊断
    issues = []
    if sd <= 1:
        issues.append("欲望: 未检测到显性欲望词(可能隐含,如'我不会让你死'隐含'守护'欲望,需 LLM 复核)")
    if so <= 1:
        issues.append("障碍: 未检测到显性障碍词(可能隐含,需 LLM 复核)")
    if sb <= 1:
        issues.append("蓄势: 未检测到显性蓄势词(张力可能通过动作/环境隐含)")
    if sr <= 1:
        issues.append("释放: 未检测到显性释放词(爆发可能靠场面而非'爆发'字样)")
    if potential < 8:
        issues.append(f"势能差偏低({potential}) → 若本章是平淡过渡章属正常;若是高潮章则偏平,需 LLM 复核")

    if not issues:
        print("\n 四拍齐全,势能差充足")
        sys.exit(0)
    print("\n诊断( 本脚本只扫显性信号词,隐含欲望/障碍靠 LLM 复核,勿当最终结论):")
    for i in issues:
        print(f"   {i}")
    print("\n补救: 显性化四拍(补欲望/障碍/蓄势/释放的直写),或 LLM 复核确认隐含。")
    sys.exit(len(issues))


if __name__ == "__main__":
    main()
