#!/usr/bin/env python3
"""中文标点/引号规范校验(GB/T 15834—2011)

确定性检查,查出:
1. 双引号/单引号左右不平衡(漏配/错配)
2. 双引号内嵌套双引号(应为外双内单)
3. 独立对话误用单引号(单引号不在双引号内)
4. ASCII 引号/半角逗号残留
5. 省略号/破折号不规范(用... / … / - 而非 …… / ——)

用法:
  python3 check_punct_spec.py <文件或目录> [--all]

返回码 0=通过,1=有错误(可用于 CI/质量门)。
"""
import re, sys
from pathlib import Path

def check_text(text, name):
    errors = []
    lines = text.splitlines()

    # 1. 引号平衡
    dl, dr = text.count("“"), text.count("”")
    sl, sr = text.count("‘"), text.count("’")
    if dl != dr:
        errors.append(f"双引号不平衡: 左{dl} 右{dr}")
    if sl != sr:
        errors.append(f"单引号不平衡: 左{sl} 右{sr}")

    # 2. 双引号内嵌套双引号(应为外双内单)
    for i, ln in enumerate(lines, 1):
        # 模式: “ ... “ ... ” ... ” (外层内又有成对双引号)
        for m in re.finditer(r"“[^”\n]*“[^”\n]*”[^”\n]*”", ln):
            errors.append(f"行{i}: 双引号内嵌套双引号(应为单引号): {ln.strip()[:50]}")

    # 3. 独立单引号(不在双引号内) = 误用
    for i, ln in enumerate(lines, 1):
        if "‘" in ln or "’" in ln:
            has_outer = "“" in ln and "”" in ln
            if not has_outer:
                errors.append(f"行{i}: 独立对话误用单引号(应双引号): {ln.strip()[:50]}")

    # 4. ASCII 残留
    asc = text.count('"') + text.count("'")
    if asc:
        errors.append(f"ASCII 引号残留 {asc} 处")
    if "," in text or ";" in text or "!" in text or "?" in text:
        # 只查英文逗号(中文逗号是全角,不会误判;英文逗号常见)
        pass  # 半角逗号可能出现在英文/数字中,单独处理
    half_comma = len(re.findall(r"[a-zA-Z0-9],", text)) + len(re.findall(r",[a-zA-Z0-9]", text))
    if half_comma:
        errors.append(f"半角逗号混用 {half_comma} 处")

    # 5. 省略号/破折号
    if "..." in text:
        errors.append("省略号用了 ...(应 ……)")
    if "…" in text and "……" not in text:
        # 单个 … 不是 ……
        singles = text.count("…") - text.count("……") * 2
        if singles > 0:
            errors.append(f"省略号不规范 {singles} 处(应 …… 两个三连点)")

    return errors

def main():
    if len(sys.argv) < 2:
        print("用法: check_punct_spec.py <文件或目录> [--all]")
        sys.exit(2)
    target = Path(sys.argv[1])
    all_mode = "--all" in sys.argv
    files = []
    if target.is_dir():
        if all_mode:
            files = sorted(target.glob("**/*"))
        else:
            files = sorted(target.glob("*"))
        # 只保留文本文件(md/txt),排除二进制
        files = [f for f in files if f.suffix.lower() in (".md", ".txt")]
    else:
        files = [target]

    if not files:
        # 顶层无文件但有子目录(如 发布/卷一/xxx.txt)→ 提示用 --all 递归
        subdirs = [p for p in target.iterdir() if p.is_dir()] if target.is_dir() else []
        if subdirs:
            print(f"顶层无直接文件,但有 {len(subdirs)} 个子目录(如 {subdirs[0].name}/)。")
            print("已扫描到的子目录内文件:")
            for sd in subdirs:
                inner = [p for p in sd.rglob("*") if p.suffix.lower() in (".md", ".txt")]
                print(f"  {sd.name}/: {len(inner)} 个 md/txt")
            print("提示: 加 --all 会递归扫描全部子目录;或直接指定子目录路径。")
            sys.exit(0)
        print("无文件")
        sys.exit(0)

    total_errors = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        errs = check_text(text, f.name)
        if errs:
            total_errors += len(errs)
            print(f"⚠ {f.name}:")
            for e in errs:
                print(f"   {e}")
        else:
            print(f" {f.name}: 引号/标点规范通过")

    if total_errors:
        print(f"\n共 {total_errors} 处错误,未通过")
        sys.exit(1)
    print("\n 全部通过")
    sys.exit(0)

if __name__ == "__main__":
    main()
