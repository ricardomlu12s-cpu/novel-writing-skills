#!/usr/bin/env python3
"""叙事 AI 味检测器 — 多语言。确定性检测 7 类模式,零成本优先。

词表外置: remove-ai-tone/locale/<语言>.json。方法论语言无关,词表按语言加载。

用法:
  python3 detect_aislop.py <文件.txt>                 # 自动识别语言(默认中文)
  python3 detect_aislop.py <文件.txt> --locale en     # 指定英文词表
  python3 detect_aislop.py <文件.txt> --locale fr     # 用法语词表(无词表则仅结构检测)

输出:命中模式清单 + 行号 + 命中词。无命中 → 无需大改。
"""
import json
import re
import sys
from pathlib import Path

LOCALE_DIR = Path(__file__).resolve().parent.parent / "locale"
DEFAULT_LOCALE = "zh"

# 语言无关的结构正则(任何语言通用)
# 非人感结构: 万能意象/哲理收尾/机械对称 等,由 LLM 兜底,这里不做正则(见 references)


def load_locale(lang):
    """加载词表。无词表文件则返回 None(仅做语言无关检测)。"""
    p = LOCALE_DIR / f"{lang}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def list_locales():
    out = []
    if LOCALE_DIR.is_dir():
        for f in sorted(LOCALE_DIR.glob("*.json")):
            try:
                meta = json.loads(f.read_text(encoding="utf-8")).get("_meta", {})
                filled = bool(meta and any(
                    json.loads(f.read_text(encoding="utf-8")).get(k)
                    for k in ("ai_only", "ai_words") if k in json.loads(f.read_text(encoding="utf-8"))
                ))
                out.append((f.stem, meta.get("name", f.stem), filled))
            except (ValueError, OSError):
                out.append((f.stem, f.stem, False))
    return out


def detect_lang(text):
    """简单语言识别: 含中文字符 → zh,否则 en(启发式)。"""
    if re.search(r"[一-鿿]", text):
        return "zh"
    return "en"


def strength_sanitization_check(text, conflict_signals, force_words):
    """文本级:冲突信号存在但直写力度词为 0 → 力度被净化。无词表则跳过。"""
    if not conflict_signals or not force_words:
        return (False, None)
    conflict_kinds = sum(1 for w in conflict_signals if w in text)
    force_kinds = sum(1 for w in force_words if w in text)
    if conflict_kinds >= 3 and force_kinds == 0:
        return (True, f"conflict signals {conflict_kinds}, force words 0")
    return (False, None)


def scan(text, loc):
    """按词表扫描。loc=None 时仅结构检测。"""
    lines = text.splitlines()
    hits = []
    if loc is None:
        return hits

    ai_only = loc.get("ai_only", [])
    ai_words = loc.get("ai_words", [])
    weak_adv = loc.get("weak_adv", [])
    inflate = loc.get("inflate", [])
    cliche = loc.get("cliche_conclusion", [])
    paperish = loc.get("paperish", [])
    formal = loc.get("formal", [])
    pacify = loc.get("pacify", [])
    whitewash = loc.get("whitewash", [])
    harmonize = loc.get("harmonize", [])
    triple_pat = loc.get("triple_pattern", "")

    triple_re = re.compile(triple_pat) if triple_pat else None

    for i, line in enumerate(lines, 1):
        for w in ai_only:
            if w in line:
                hits.append((i, "AI专属(身份指纹)", w))
        for w in ai_words + weak_adv + inflate + cliche + paperish + formal:
            if w in line:
                mode = (1 if w in ai_words else 2 if w in weak_adv else 3 if w in inflate
                        else 4 if w in cliche else 5 if w in paperish else 6)
                hits.append((i, f"模式{mode}", w))
        if triple_re:
            for m in triple_re.finditer(line):
                hits.append((i, "模式7-排比三连", m.group()))
        for w in pacify:
            if w in line:
                hits.append((i, "反净化-化解冲突", w))
        for w in whitewash:
            if w in line:
                hits.append((i, "反净化-洗白化", w))
        for w in harmonize:
            if w in line:
                hits.append((i, "反净化-过度圆满", w))
    return hits


def main():
    args = [a for a in sys.argv[1:]]
    if not args:
        print("用法: detect_aislop.py <文件.txt> [--locale en|zh|ja|ru|...]")
        print("可选: --list-locales 查看已有语言词表")
        sys.exit(1)

    if "--list-locales" in args:
        print("可用语言词表:")
        for code, name, filled in list_locales():
            status = "完整" if filled else "空模板(仅结构检测)"
            print(f"  {code}: {name} [{status}]")
        sys.exit(0)

    text = Path(args[0]).read_text(encoding="utf-8")

    lang = DEFAULT_LOCALE
    if "--locale" in args:
        lang = args[args.index("--locale") + 1]
    else:
        lang = detect_lang(text)

    loc = load_locale(lang)
    if loc is None:
        print(f" 无 {lang} 词表(locale/{lang}.json 不存在),仅做语言无关结构检测。")
        print("   贡献词表见 CONTRIBUTING-locales.md")
        hits = []
        conflict_signals = force_words = []
    else:
        hits = scan(text, loc)
        conflict_signals = loc.get("conflict_signals", [])
        force_words = loc.get("force_words", [])

    hit_strength, strength_note = strength_sanitization_check(text, conflict_signals, force_words)

    if not hits and not hit_strength:
        print(" 未检测到显著 AI 味模式")
        return
    if hits:
        print(f" 命中 {len(hits)} 处:")
        by_mode = {}
        for line, mode, word in hits:
            by_mode.setdefault(mode, []).append((line, word))
            print(f"  L{line} [{mode}] {word}")
        print("\n建议:命中多的模式优先改写,再跑第二遍 AI 自审。")
        print("注意:「反净化-*」命中 ≠ 一定错,须 LLM 兜底核对是否有铺垫/是否合理。")
    if hit_strength:
        print(f"\n 力度净化提示: {strength_note} — 有激烈冲突却无任何直写力度词,可能被写轻了。克制文风可豁免,须 LLM 兜底判断。")


if __name__ == "__main__":
    main()
