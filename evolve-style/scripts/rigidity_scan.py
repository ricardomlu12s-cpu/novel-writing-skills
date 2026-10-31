#!/usr/bin/env python3
"""rigidity_scan.py — 防固化扫描(evolve-style)
检测六大表层维度(句式/用语/修辞/词汇/表达/写作手法)是否被模仿锁死。
偏差≈0(接近目标指纹) → 锁死区告警 → 主动去中心化。
用法:
  python3 rigidity_scan.py <项目目录>
  缺 style-library 目标指纹时降级为"内部重复度"检测(仍能发现复读/同构)。
"""
import os
import re
import sys

# 目标指纹文件可能的位置: 不再硬编码风格库名,扫描 assets/style 下所有子目录
STYLE_LIB_NAMES = None  # None = 动态扫描;可显式指定为 tuple 覆盖


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


def find_target_fingerprint(proj):
    lib = os.environ.get("ASSET_ROOT") or os.path.expanduser("~/.omc/assets")
    # 兼容旧 style-library 位置 + 新 assets/style 位置
    bases = [os.path.expanduser("~/.omc/style-library"), os.path.join(lib, "style")]
    for base in bases:
        if not os.path.isdir(base):
            continue
        names = STYLE_LIB_NAMES or sorted(os.listdir(base))
        for name in names:
            fp = os.path.join(base, name, "fingerprint.md")
            if os.path.isfile(fp):
                return fp
    # 项目内也可能有
    for cand in ("style-library", ".style-library"):
        p = os.path.join(proj, cand)
        if os.path.isdir(p):
            for f in os.listdir(p):
                if f.endswith(".md"):
                    return os.path.join(p, f)
    return None


def zh_sentences(text):
    # 以中英文句号/叹号/问号/换行切句
    parts = re.split(r"[。！？!?；;\n]", text)
    return [p.strip() for p in parts if len(p.strip()) >= 2]


def split_words(text):
    # 中文按字符成词 + 英文按空格
    words = re.findall(r"[一-鿿]|[A-Za-z]+", text)
    return words


def chunk_stats(text):
    """句长/段长/标点密度/对白占比 等表层特征。"""
    sents = zh_sentences(text)
    if not sents:
        return None
    avg_len = sum(len(s) for s in sents) / len(sents)
    # 句长方差
    var_len = sum((len(s) - avg_len) ** 2 for s in sents) / len(sents)
    paras = [p for p in text.split("\n\n") if p.strip()]
    if paras:
        para_avg = sum(len(p) for p in paras) / len(paras)
        short_ratio = sum(1 for p in paras if len(p) <= 20) / len(paras)
    else:
        para_avg, short_ratio = 0.0, 0.0
    ellipsis = text.count("……")
    ellipsis_per = ellipsis / max(len(text), 1) * 10000
    quotes = re.findall(r"“.*?”", text)
    dialog_ratio = sum(len(q) for q in quotes) / max(len(text), 1)
    return {
        "sents": len(sents),
        "avg_len": round(avg_len, 2),
        "var_len": round(var_len, 1),
        "para_avg": round(para_avg, 1),
        "short_ratio": round(short_ratio, 3),
        "ellipsis_per": round(ellipsis_per, 2),
        "dialog_ratio": round(dialog_ratio, 3),
    }


def top_ngrams(text, n, k=12):
    words = split_words(text)
    grams = {}
    for i in range(len(words) - n + 1):
        g = "".join(words[i:i + n])
        grams[g] = grams.get(g, 0) + 1
    return sorted(grams.items(), key=lambda x: -x[1])[:k]


def scan_internal(texts):
    """内部重复度:复读高频词/同构句,即使无目标指纹也能发现固化。"""
    if not texts:
        return {"status": "no_text"}
    full = "\n".join(texts)
    wc = len(full)
    if wc < 200:
        return {"status": "too_short"}

    # 高频词 top
    words = split_words(full)
    freq = {}
    for w in words:
        if len(w) == 1:
            continue
        freq[w] = freq.get(w, 0) + 1
    top_words = sorted(freq.items(), key=lambda x: -x[1])[:15]

    # 高频二字词(可能是口头禅/连接词锁死)
    bi = top_ngrams(full, 2, 10)

    # 同构句式:句首两字重复(如"他走…他看…")
    sents = zh_sentences(full)
    lead = {}
    for s in sents:
        l2 = s[:2]
        lead[l2] = lead.get(l2, 0) + 1
    top_lead = sorted(lead.items(), key=lambda x: -x[1])[:10]

    # 修辞复用:破折号/叹号密度
    dash = full.count("——")
    excl = full.count("!")

    return {
        "status": "internal",
        "chars": wc,
        "top_words": top_words,
        "top_bigrams": bi,
        "top_sentence_leads": top_lead,
        "dash": dash,
        "excl": excl,
    }


def scan_against_target(texts, fp_path):
    try:
        with open(fp_path, encoding="utf-8") as fh:
            target = fh.read()
    except OSError:
        return None
    if not target.strip():
        return None
    actual = chunk_stats("\n".join(texts)) if texts else None
    target_stats = chunk_stats(target)
    if not actual or not target_stats:
        return None

    # 六个维度的偏差(目标无该特征时该维度不参与对比)
    def pct(a, b):
        # 目标为0 → 无对照基准,返回 None 不参与平均
        if b == 0:
            return None
        return abs(a - b) / b * 100

    dims = {
        "句式": pct(actual["avg_len"], target_stats["avg_len"]),
        "表达": pct(actual["dialog_ratio"], target_stats["dialog_ratio"]),
        "修辞": pct(actual["ellipsis_per"], target_stats["ellipsis_per"]),
        "节奏": pct(actual["short_ratio"], target_stats["short_ratio"]),
    }
    # 偏差均值(只对"目标有基准"的维度平均)
    vals = [v for v in dims.values() if v is not None]
    avg_dev = sum(vals) / len(vals) if vals else 0.0

    # 锁死区判定:偏差均值 < 阈值(默认 20% → 表达固化)
    locked = avg_dev < 20.0
    # 失控区:偏差均值 > 80%(脱离基准)
    runaway = avg_dev > 80.0
    return {"avg_dev": round(avg_dev, 1), "dims": dims, "locked": locked,
            "runaway": runaway, "actual": actual, "target": target_stats}


def main():
    if len(sys.argv) < 2:
        print("用法: rigidity_scan.py <项目目录>")
        sys.exit(1)
    proj = os.path.abspath(sys.argv[1])
    texts = collect_manuscripts(proj)

    if not texts:
        print("项目:", proj)
        print("未找到 manuscripts/,跳过")
        sys.exit(0)

    fp = find_target_fingerprint(proj)
    if fp:
        res = scan_against_target(texts, fp)
        if res:
            print("项目:", proj)
            print("目标指纹:", fp)
            print("实际: 句长", res["actual"]["avg_len"],
                  "对白", res["actual"]["dialog_ratio"],
                  "省略号密度", res["actual"]["ellipsis_per"])
            print("目标: 句长", res["target"]["avg_len"],
                  "对白", res["target"]["dialog_ratio"],
                  "省略号密度", res["target"]["ellipsis_per"])
            print("六维偏差:", res["dims"])
            print("平均偏差:", res["avg_dev"], "%")
            if res["locked"]:
                print("▶ 锁死区告警:偏差≈0,表达固化 → 主动去中心化(新手法/陌生化/限用令)")
            elif res["runaway"]:
                print("▶ 失控区:偏差过大,脱离基准 → 拉回(防漂移)")
            else:
                print("▶ 健康区:中等偏差,个人化正在形成 → 正常进化")
            sys.exit(0)

    # 无目标指纹 → 内部重复度
    res = scan_internal(texts)
    if res.get("status") == "no_text":
        print("未找到文本")
    elif res.get("status") == "too_short":
        print("文本过短,跳过")
    else:
        print("项目:", proj)
        print("无目标指纹,内部重复度扫描:")
        print("  高频词 top:", res["top_words"][:8])
        print("  高频二字词 top:", res["top_bigrams"][:6])
        print("  同构句首 top:", res["top_sentence_leads"][:6])
        print("  破折号:", res["dash"], "| 叹号:", res["excl"])
        # 内部复读告警:高频词占比过高
        if res["top_words"] and res["chars"] > 0:
            top_word_ratio = sum(c for _, c in res["top_words"][:5]) / res["chars"]
            if top_word_ratio > 0.05:
                print("▶ 内部复读告警:高频词集中 → 限用令/换词")


if __name__ == "__main__":
    main()
