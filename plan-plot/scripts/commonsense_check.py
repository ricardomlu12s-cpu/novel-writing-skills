#!/usr/bin/env python3
"""常识合理性检测 — 确定性规则优先,特殊题材豁免。

用法:
  python3 commonsense_check.py <章节.txt> [--genre 玄幻|科幻|历史架空|现实]

默认 --genre 现实(从严)。特殊题材显式标,否则按现实误报。
"""
import sys, re
from pathlib import Path

# 时空矛盾信号(现实题材)
TRANSIT = ["瞬移", "一个呼吸间", "转眼就到了", "眨眼间来到", "一炷香功夫就到了"]
# 物理/体力异常(现实题材)
PHYSICS = ["三天三夜没睡", "七天七夜", "不吃不喝", "一个月没睡"]
# 因果巧合(无铺垫)
COINCIDENCE = ["恰好", "正巧", "偏偏这时候", "刚好路过", "恰巧"]

GENRES = {
    "玄幻": {"豁免": ["物理", "人体"], "从严": ["因果", "社会", "时空"]},
    "科幻": {"豁免": ["物理"], "从严": ["因果", "逻辑"]},
    "历史架空": {"豁免": ["历史地理"], "从严": ["物理", "因果", "社会"]},
    "现实": {"豁免": [], "从严": ["物理", "时空", "人体", "因果", "社会", "历史地理"]},
}

def check(text, genre):
    lines = text.splitlines()
    hits = []
    exempt = GENRES.get(genre, GENRES["现实"])["豁免"]
    strict = GENRES.get(genre, GENRES["现实"])["从严"]
    for i, line in enumerate(lines, 1):
        for w in TRANSIT:
            if w in line and "时空" in strict:
                hits.append((i, "时空", f"疑似瞬移/空间异常「{w}」({genre}题材{'豁免' if '时空' in exempt else '需设定支撑'})"))
        for w in PHYSICS:
            if w in line and "人体" in strict:
                hits.append((i, "人体", f"体力/生理异常「{w}」({genre}题材{'豁免' if '人体' in exempt else '需设定支撑'})"))
        for w in COINCIDENCE:
            if w in line and "因果" in strict:
                hits.append((i, "因果", f"无铺垫巧合「{w}」({genre}题材{'豁免' if '因果' in exempt else '需伏笔'})"))
    return hits

def main():
    if len(sys.argv) < 2:
        print("用法: commonsense_check.py <章节.txt> [--genre 玄幻|科幻|历史架空|现实]")
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    genre = "现实"
    if "--genre" in sys.argv:
        idx = sys.argv.index("--genre")
        genre = sys.argv[idx+1] if idx+1 < len(sys.argv) else "现实"
    hits = check(text, genre)
    if not hits:
        print(f" 未检测到违常识写法(题材: {genre})")
        return
    print(f" 检测到 {len(hits)} 处违常识(题材: {genre}):")
    for line, dim, msg in hits:
        print(f"  L{line} [{dim}] {msg}")
    print("\n提示:若属特殊题材豁免维度,忽略;若违常识,LLM 判断是否需要设定支撑或改写。")

if __name__ == "__main__":
    main()
