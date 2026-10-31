#!/usr/bin/env python3
"""fingerprint_scan.py — 实际指纹扫描(evolve-style)
统计已写定稿的风格特征,输出"实际指纹"(与目标指纹同构,供双轨对比)。
用法:
  python3 fingerprint_scan.py <项目目录>
"""
import os
import re
import sys


def collect_manuscripts(proj):
    mdir = os.path.join(proj, "manuscripts")
    texts = []
    if os.path.isdir(mdir):
        for f in sorted(os.listdir(mdir)):
            if re.match(r"^ch\d{3}\.md$", f):
                try:
                    with open(os.path.join(mdir, f), encoding="utf-8") as fh:
                        texts.append(fh.read())
                except OSError:
                    pass
    return texts


def zh_sentences(text):
    parts = re.split(r"[。！？!?；;\n]", text)
    return [p.strip() for p in parts if len(p.strip()) >= 2]


def compute_fingerprint(text):
    """输出与目标指纹同构的实际指纹六维 + 五维句法特征。"""
    sents = zh_sentences(text)
    total_chars = max(len(text), 1)

    avg_len = sum(len(s) for s in sents) / len(sents) if sents else 0
    var_len = (sum((len(s) - avg_len) ** 2 for s in sents) / len(sents)
               if sents else 0)

    paras = [p for p in text.split("\n\n") if p.strip()]
    short_ratio = (sum(1 for p in paras if len(p) <= 20) / len(paras)
                   if paras else 0)

    ellipsis = text.count("……")
    dash = text.count("——")
    quotes = re.findall(r"“.*?”", text)
    dialog_ratio = sum(len(q) for q in quotes) / total_chars

    # 情感浓度:情绪词频(简单词典)
    emotion_words = ["愤怒", "害怕", "悲伤", "开心", "激动", "绝望",
                     "温柔", "心痛", "恐惧", "狂喜", "痛苦", "不安"]
    emotion_hits = sum(text.count(w) for w in emotion_words)
    emotion_density = emotion_hits / total_chars * 1000

    # 五维句法特征
    excl = text.count("！") + text.count("!")
    quest = text.count("？") + text.count("?")

    fingerprint = {
        "sents": len(sents),
        "avg_len": round(avg_len, 2),
        "var_len": round(var_len, 1),
        "short_ratio": round(short_ratio, 3),
        "ellipsis_per": round(ellipsis / total_chars * 10000, 2),
        "dash_per": round(dash / total_chars * 10000, 2),
        "dialog_ratio": round(dialog_ratio, 3),
        "emotion_density": round(emotion_density, 2),
        "excl_per": round(excl / total_chars * 10000, 2),
        "quest_per": round(quest / total_chars * 10000, 2),
    }
    return fingerprint


def main():
    if len(sys.argv) < 2:
        print("用法: fingerprint_scan.py <项目目录>")
        sys.exit(1)
    proj = os.path.abspath(sys.argv[1])
    texts = collect_manuscripts(proj)
    if not texts:
        print("项目:", proj)
        print("未找到 manuscripts/,跳过")
        sys.exit(0)

    fp = compute_fingerprint("\n".join(texts))
    print("项目:", proj)
    print(f"已写: {len(texts)} 章")
    print("实际指纹(与目标指纹同构):")
    for k, v in fp.items():
        print(f"  {k}: {v}")

    # 按章输出(看变化趋势)
    print("\n分章特征:")
    for i, t in enumerate(texts, 1):
        f = compute_fingerprint(t)
        print(f"  ch{i:03d}: 句长 {f['avg_len']:.1f} 对白 {f['dialog_ratio']:.2f} "
              f"省略号 {f['ellipsis_per']:.1f} 短段 {f['short_ratio']:.2f}")


if __name__ == "__main__":
    main()
