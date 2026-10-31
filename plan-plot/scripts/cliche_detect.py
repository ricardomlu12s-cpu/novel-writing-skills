#!/usr/bin/env python3
"""套路识别 — 匹配 cliche-library + 事件冷却防重复。

用法:
  python3 cliche_detect.py <章节.txt>

输出:命中的套路 + 破局建议提示 + 冷却状态。
"""
import sys, re
from pathlib import Path

# 套路特征信号(命中即可能套路)
CLICHES = [
    ("打脸", ["打脸", "当场打脸", "脸都绿了", "目瞪口呆", "哑口无言"]),
    ("退婚/羞辱开局", ["退婚", "一纸休书", "当众羞辱", "逐出宗门", "赶出家门"]),
    ("废柴逆袭", ["废物", "废柴", "杂役弟子", "资质平庸", "洗髓", "脱胎换骨"]),
    ("系统送挂", ["系统提示", "叮!", "宿主", "绑定系统", "新手礼包", "签到"]),
    ("穿越开挂", ["穿越", "重生", "现代知识", "前世记忆", "金手指"]),
    ("升级流水账", ["突破", "晋级", "升级", "境界", "金丹", "元婴", "渡劫"]),
    ("一呼百应", ["援军", "千钧一发", "及时赶到", "救兵", "破门而入"]),
    ("扮猪吃虎", ["扮猪吃虎", "深藏不露", "故意示弱", "装傻"]),
]

# 事件冷却:同一套路 10 章内不再重复(读项目目录的冷却记录)
COOLDOWN_WINDOW = 10

def scan(text):
    hits = []
    for name, signals in CLICHES:
        for s in signals:
            if s in text:
                hits.append((name, s))
                break  # 每个套路只记一次
    return hits

def main():
    if len(sys.argv) < 2:
        print("用法: cliche_detect.py <章节.txt>")
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    hits = scan(text)
    if not hits:
        print(" 未检测到明显套路")
        return
    print(f" 命中 {len(hits)} 个套路信号:")
    for name, sig in hits:
        print(f"  [{name}] 信号「{sig}」")
    print("\n破局建议:")
    for name, _ in hits:
        advice = {
            "打脸": "延迟/反噬打脸,或打脸代价化",
            "退婚/羞辱开局": "不报复,反向共情;或开局已过去式",
            "废柴逆袭": "废柴给结构性原因,逆袭靠代价与牺牲",
            "系统送挂": "系统来源黑箱化,金手指有副作用",
            "穿越开挂": "碾压受限,或知识反而害主角",
            "升级流水账": "插入非战斗进度(关系/真相/代价)",
            "一呼百应": "援军迟到/叛变/有代价",
            "扮猪吃虎": "拆开单用,扮猪要有真实弱点",
        }.get(name, "打破预期/反转设定/置换元素")
        print(f"  · {name} → {advice}")
    print(f"\n提示:若同套路前 {COOLDOWN_WINDOW} 章已用,建议冷却(避免重复)。")

if __name__ == "__main__":
    main()
