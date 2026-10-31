#!/usr/bin/env python3
"""非人感结构扫描器 — 抓"人类不会这样写"的结构特征,非词表;带豁免区保护玩梗。

用法:
  python3 non_human_scan.py <章节.txt> [--exempt <豁免区.jsonl>]

输出:句法模板命中(密度)+ 分布异常 + 堆叠vs点缀判定。
"""
import sys, re, json
from pathlib import Path

# 句法模板(正则抓结构,非词表)
SYNTAX_TEMPLATES = [
    ("递进句式", re.compile(r"(不仅仅|不只是|不仅)\S{0,12}(更是|而是|而且)")),
    ("修饰模板", re.compile(r"以一种\S{0,8}(姿态|方式)")),
    ("万能意象", re.compile(r"(仿佛|时间)\S{0,8}(凝固|静止|停滞)")),
    ("拟人过度", re.compile(r"\S{2,6}仿佛在诉说着?")),
    ("哲理收尾", re.compile(r"(这一夜|那一刻|或许)，?\S{0,8}(明白|真谛)")),
    ("排比三连", re.compile(r"[一-鿿]{2,4}(?:、[一-鿿]{2,4}){2,}(?:\s*[,，。]|$)")),
]

# 升华信号(结尾总结句)
ELEVATION_SIGNS = ["他明白了", "终于明白", "或许", "的真谛", "这一刻起", "从此", "懂得了"]

def load_exempt(path):
    if not path:
        return set()
    exprs = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            exprs.add(json.loads(line).get("expr", ""))
        except json.JSONDecodeError:
            pass
    return exprs

def scan(text, exempt):
    paras = [p for p in text.split("\n\n") if p.strip()]
    results = []
    exempt_hits = 0
    for pi, para in enumerate(paras):
        para_hits = []
        for name, rx in SYNTAX_TEMPLATES:
            for m in rx.finditer(para):
                hit = m.group()
                if hit in exempt:
                    exempt_hits += 1
                    continue
                para_hits.append((name, hit))
        if para_hits:
            results.append((pi, para_hits))
    return results, exempt_hits

def distribution(text):
    """分布异常:句长方差 + 升华率"""
    sents = [s for s in re.split(r"[。！？!?…]", text) if len(s) > 1]
    stats = {}
    if sents:
        lens = [len(s) for s in sents]
        avg = sum(lens) / len(lens)
        var = (sum((l-avg)**2 for l in lens) / len(lens)) ** 0.5
        stats["sentence_var"] = round(var, 1)
        stats["sentence_var_low"] = var < 3
    # 升华率(粗略:含升华信号的结尾句子占比)
    elev = sum(1 for s in sents if any(sig in s for sig in ELEVATION_SIGNS))
    stats["elevation_rate"] = round(elev / len(sents), 2) if sents else 0
    stats["elevation_high"] = (elev / len(sents)) > 0.4 if sents else False
    return stats

def main():
    if len(sys.argv) < 2:
        print("用法: non_human_scan.py <章节.txt> [--exempt <豁免区.jsonl>]")
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    exempt = set()
    if "--exempt" in sys.argv:
        idx = sys.argv.index("--exempt")
        exempt = load_exempt(sys.argv[idx+1] if idx+1 < len(sys.argv) else None)

    results, exempt_hits = scan(text, exempt)
    stats = distribution(text)

    print(f"=== 分布异常 ===")
    print(f"句长方差: {stats.get('sentence_var','-')} ({'低→AI腔' if stats.get('sentence_var_low') else '正常'})")
    print(f"升华率: {stats.get('elevation_rate','-')} ({'过高→机械' if stats.get('elevation_high') else '正常'})")

    if not results:
        print(f"\n 未检测到模板堆叠(豁免 {exempt_hits} 处)")
        return
    print(f"\n=== 句法模板命中({len(results)} 段,豁免 {exempt_hits} 处) ===")
    for pi, hits in results:
        for name, hit in hits:
            print(f"  段{pi} [{name}] {hit[:40]}")
    # 密度判定:模板命中数 / 段落数
    total_hits = sum(len(h) for _, h in results)
    density = total_hits / max(1, len(results))
    if density >= 1.5:
        print(f"\n 模板堆叠(密度 {density:.1f}/段)→ 非人感,建议改写")
    else:
        print(f"\n 低密度(密度 {density:.1f}/段)→ 可能是点缀/玩梗,不告警")

if __name__ == "__main__":
    main()
