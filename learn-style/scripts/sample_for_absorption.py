#!/usr/bin/env python3
"""多维吸收采样 — 从作品全文定位 5-15 个代表片段(按维度),产出采样清单。

用法:
  python3 sample_for_absorption.py <作品文件.txt> [--max_chars 20000]

输出:
  - 全貌扫描统计(句长/标点/高频词)
  - 按 7 维定位的代表片段清单(段落起止 + 维度标注)
  - 学习价值画像(最强维度)
"""
import sys, re
from pathlib import Path
from collections import Counter

# 各维度定位信号
DIM_SIGNALS = {
    "语言": ["仿佛", "宛如", "像", "如", "如同", "似", "好像", "比喻"],
    "内涵": ["意义", "人生", "命运", "信念", "道", "真理", "为何", "何为", "选择", "代价"],
    "人物": ["他说", "她说", "道", "想", "心", "记忆", "幼时", "从前", "我曾"],
    "情节": ["轰", "爆", "惊", "反转", "死", "真相", "竟然", "原来", "危险", "杀"],
    "世界观": ["规则", "境界", "灵气", "战力", "法则", "宗门", "系统", "位面", "功法"],
    "情感": ["哭", "泪", "痛", "怒", "恨", "爱", "暖", "绝望", "颤抖", "悲"],
}
# 风格维度:分散取,用句长/标点统计特征定位(这里以段落长度与句长为代理)
EMOTION_WORDS = ["哭", "泪", "痛", "怒", "恨", "爱", "暖", "绝望", "颤抖", "悲", "燃", "爽"]

def split_paragraphs(text):
    """按空行/换行切段落,返回 [(段落文本, 起始offset)]"""
    paras = []
    cur = []
    start = 0
    offset = 0
    for line in text.splitlines():
        if line.strip():
            if not cur:
                start = offset
            cur.append(line)
        else:
            if cur:
                paras.append(("\n".join(cur), start))
                cur = []
        offset += len(line) + 1
    if cur:
        paras.append(("\n".join(cur), start))
    return paras

def sentence_lens(text):
    """粗算句长分布(按句号/感叹号/问号/省略号切)"""
    sents = re.split(r"[。！？!?…]", text)
    return [len(s) for s in sents if len(s) > 1]

def scan(text, paras):
    """全貌扫描统计 + 每段信号评分"""
    stats = {}
    sents = sentence_lens(text)
    stats["avg_sent_len"] = round(sum(sents)/len(sents), 1) if sents else 0
    stats["sent_len_var"] = round((sum((l-(sum(sents)/len(sents)))**2 for l in sents)/len(sents))**0.5, 1) if sents else 0
    # 标点
    stats["comma"] = text.count("，") + text.count(",")
    stats["ellipsis"] = text.count("…") + text.count("……")
    stats["dash"] = text.count("——") + text.count("—")
    # 高频词
    words = re.findall(r"[一-鿿]{2,4}", text)
    stats["top_words"] = [w for w, c in Counter(words).most_common(12)]
    # 段落信号评分
    scored = []
    for p, off in paras:
        s = {"para": p, "off": off, "len": len(p), "signals": {}}
        for dim, sigs in DIM_SIGNALS.items():
            s["signals"][dim] = sum(1 for sig in sigs if sig in p)
        s["emotion"] = sum(1 for w in EMOTION_WORDS if w in p)
        scored.append(s)
    return stats, scored

def select_samples(scored, max_chars=20000):
    """按维度选代表片段(每维取信号最强的 1-3 段),控制总字数"""
    selected = {}
    used_offs = set()
    # 语言/内涵/人物/情节/世界观/情感:取信号最强且未用的
    for dim in ["语言", "内涵", "人物", "情节", "世界观", "情感"]:
        ranked = [s for s in sorted(scored, key=lambda x: (-x["signals"][dim], -x["len"]))
                  if s["signals"][dim] > 0 and s["off"] not in used_offs]
        take = ranked[:2]
        for s in take:
            used_offs.add(s["off"])
            selected.setdefault(dim, []).append(s)
    # 风格:分散取(前/中/后各一段)
    n = len(scored)
    if n:
        for idx in ([0, n//2, n-1] if n >= 3 else [0, n-1][:n]):
            s = scored[idx]
            if s["off"] not in used_offs:
                used_offs.add(s["off"])
                selected.setdefault("风格", []).append(s)
    return selected

def value_profile(selected):
    """学习价值画像:统计每维选中片段数 + 信号强度,标最强维度"""
    strengths = {}
    for dim, items in selected.items():
        strengths[dim] = sum(sum(s["signals"].values()) for s in items) + sum(len(s["para"]) for s in items)//200
    if not strengths:
        return {}
    ranked = sorted(strengths.items(), key=lambda x: -x[1])
    return {dim: round(score, 1) for dim, score in ranked}

def main():
    if len(sys.argv) < 2:
        print("用法: sample_for_absorption.py <作品文件.txt> [--max_chars 20000]")
        sys.exit(1)
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    max_chars = 20000
    if "--max_chars" in sys.argv:
        idx = sys.argv.index("--max_chars")
        max_chars = int(sys.argv[idx+1]) if idx+1 < len(sys.argv) else 20000
    paras = split_paragraphs(text)
    stats, scored = scan(text, paras)
    selected = select_samples(scored, max_chars)

    print(f"=== 全貌扫描 ===")
    print(f"总字数: {len(text)} | 段落数: {len(paras)}")
    print(f"均句长: {stats['avg_sent_len']} | 句长方差: {stats['sent_len_var']}")
    print(f"逗号:{stats['comma']} 省略号:{stats['ellipsis']} 破折号:{stats['dash']}")
    print(f"高频词: {', '.join(stats['top_words'][:8])}")
    print(f"句长方差低(<3) + 省略号少 → 可能是AI腔(去AI味检查)")

    print(f"\n=== 多维采样({sum(len(v) for v in selected.values())} 段) ===")
    total = 0
    for dim, items in selected.items():
        for s in items:
            total += len(s["para"])
            preview = s["para"][:60].replace("\n", " ")
            print(f"  [{dim}] {s['off']}+ 段({len(s['para'])}字): {preview}...")
    print(f"\n总采样字数: {total}(目标 ≤{max_chars})")

    print(f"\n=== 学习价值画像 ===")
    profile = value_profile(selected)
    if profile:
        ranked = list(profile.items())
        print(f"最强维度: {ranked[0][0]}(强度{ranked[0][1]})")
        print(f"次强: {ranked[1][0] if len(ranked)>1 else '-'} | 弱: {ranked[-1][0] if len(ranked)>1 else '-'}")
        print(f"建议吸收重点: {ranked[0][0]} + {ranked[1][0] if len(ranked)>1 else ''}")

if __name__ == "__main__":
    main()
