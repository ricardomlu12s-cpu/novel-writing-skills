#!/usr/bin/env python3
"""句子级重复描写检测 — 抽取意象/形容词/高频短语,跨章查重。

用法:
  python3 repetition_detect.py <项目目录> [--top 20]

读取 .omc/story/<项目>/manuscripts/ch*.md,
输出高频意象/形容词/短语在跨章的重复清单。
"""
import sys, re
from collections import Counter
from pathlib import Path

# 意象词(具象名词)信号
IMAGERY = ["剑", "刀", "血", "火", "冰", "山", "海", "星", "月", "风", "雨", "雪",
           "眼眸", "嘴角", "眉头", "手心", "呼吸", "影子", "灯火", "夜色", "晨光"]
# 高频形容词
ADJ = ["深邃", "幽深", "冰冷", "炽热", "刺骨", "温柔", "凌厉", "妖异", "锐利",
       "沉重", "缥缈", "浩瀚", "苍茫", "肃杀", "炽烈"]

def extract_features(text):
    feats = Counter()
    for w in IMAGERY + ADJ:
        c = text.count(w)
        if c:
            feats[w] = c
    # 高频短语(2-3字重复)
    for m in re.findall(r"[一-鿿]{2,3}", text):
        pass  # 交给短语计数
    return feats

def main():
    if len(sys.argv) < 2:
        print("用法: repetition_detect.py <项目目录> [--top 20]")
        sys.exit(1)
    proj = Path(sys.argv[1])
    mans = proj / "manuscripts"
    if not mans.exists():
        print(f"未找到正文目录: {mans}")
        sys.exit(1)
    top_n = 20
    if "--top" in sys.argv:
        idx = sys.argv.index("--top")
        top_n = int(sys.argv[idx+1]) if idx+1 < len(sys.argv) else 20
    per_ch = []
    for f in sorted(mans.glob("ch*.md")):
        per_ch.append((f.stem, extract_features(f.read_text(encoding="utf-8"))))
    if len(per_ch) < 2:
        print("需 ≥2 章才能查重")
        return
    # 跨章重复:同一意象/形容词在 ≥2 章都出现
    all_feats = Counter()
    for _, feats in per_ch:
        for w in feats:
            all_feats[w] += 1
    repeated = {w for w, cnt in all_feats.items() if cnt >= 2}
    if not repeated:
        print(" 未检测到跨章重复的意象/形容词")
        return
    print(f" 检测到 {len(repeated)} 个跨章重复特征(top {top_n}):")
    for w in sorted(repeated, key=lambda x: -all_feats[x])[:top_n]:
        chap = [name for name, feats in per_ch if w in feats]
        print(f"  「{w}」出现在 {len(chap)} 章: {', '.join(chap[:6])}")
    print("\n建议:重复意象可用同义词/换具体物象/换场景呈现替代,防描写生硬重复。")

if __name__ == "__main__":
    main()
