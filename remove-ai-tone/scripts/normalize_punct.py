#!/usr/bin/env python3
"""中文标点规范化 — 统一为规范中文标点,便于发表。

规范: 全角标点 ，。；：！？（） ; 引号用 “ ”(中文规范弯引号)。
修复:
1. 半角 , ; : ! ? ( )  →  全角 ， ； ： ！ ？ （ ）
2. 「 」 → “ ”(规范中文引号)
3. ASCII 双引号 " " → “ ”(成对转换)
4. 不碰句号 . (可能是小数/省略号/英文缩写,不全局改)
5. 中文标点后去除多余空格

用法:
  python3 normalize_punct.py <文件> [--inplace]
  --inplace: 直接改原文件;否则生成 <文件>.norm
"""
import re, sys
from pathlib import Path

# 半角 → 全角(标点)
PUNCT_MAP = {
    ",": "，", ";": "；", ":": "：", "!": "！", "?": "？",
    "(": "（", ")": "）",
}
# 注意: 句号 . 不进映射(避免误改小数/省略号)

def to_fullwidth_pair(text, left, right):
    """把 ASCII 双引号成对转成 中文引号"""
    out = []
    opening = True
    for ch in text:
        if ch == '"':
            out.append("“" if opening else "”")
            opening = not opening
        else:
            out.append(ch)
    return "".join(out)

def normalize(text):
    # 1. 半角 → 全角(标点)
    text = "".join(PUNCT_MAP.get(ch, ch) for ch in text)
    # 2. 「」 → “”
    text = text.replace("「", "“").replace("」", "”")
    # 3. ASCII " → “”(成对)
    text = to_fullwidth_pair(text, "“", "”")
    # 4. 破折号: 中文间的单个 - → ——
    text = re.sub(r"(?<=[一-鿿])-(?=[一-鿿])", "——", text)
    # 5. 中文标点后多余空格
    text = re.sub(r"([，。；：！？”）]) +", r"\1", text)
    return text

def main():
    if len(sys.argv) < 2:
        print("用法: normalize_punct.py <文件|项目目录> [--inplace] [--all]")
        print("  文件: 规范化单文件")
        print("  项目目录 + --all: 扫 manuscripts/ + drafts/ 全部 md(防遗漏)")
        sys.exit(1)
    target = Path(sys.argv[1])
    inplace = "--inplace" in sys.argv
    scan_all = "--all" in sys.argv

    # 目录扫描模式: 扫 manuscripts + drafts 全部 md
    if target.is_dir():
        files = []
        for sub in ("manuscripts", "drafts"):
            d = target / sub
            if d.exists():
                files.extend(sorted(d.glob("*.md")))
        if not files:
            print(f"未找到正文文件: {target}/manuscripts 或 drafts")
            sys.exit(1)
        print(f"扫描到 {len(files)} 个正文文件(manuscripts+drafts)")
        for f in files:
            process(f, inplace=True)
        print(f"\n 全部规范化完成: {len(files)} 个文件")
        return

    process(target, inplace)

def process(f, inplace):
    text = f.read_text(encoding="utf-8")
    norm = normalize(text)
    if inplace:
        f.write_text(norm, encoding="utf-8")
        print(f" 已规范化(原文件): {f}")
    else:
        out = Path(str(f) + ".norm")
        out.write_text(norm, encoding="utf-8")
        print(f" 已生成规范化文件: {out}")
    # 统计
    half_before = sum(1 for c in text if c in ",;:!?()")
    half_after = sum(1 for c in norm if c in ",;:!?()")
    corner_before = text.count("「") + text.count("」")
    corner_after = norm.count("「") + norm.count("」")
    print(f"   半角标点: {half_before} → {half_after} | 「」: {corner_before} → {corner_after}")

if __name__ == "__main__":
    main()
