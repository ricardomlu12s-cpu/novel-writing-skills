#!/usr/bin/env python3
"""定向扩窗提取 — 围绕采样偏移量 + 关键词匹配,提取上下文窗口。

用法:
  python3 extract_windows.py <作品文件.txt> <输出.txt> \
      --offsets 613127,390650,... \
      --keywords 资本,秩序,神术,体系 \
      --window 3000 --max_windows 14
"""
import sys, re
from pathlib import Path

def parse_args(argv):
    opts = {"offsets": [], "keywords": [], "window": 3000, "max_windows": 14}
    i = 0  # argv 传入时为去掉 program/源/目标 的切片,选项从索引 0 开始
    while i < len(argv):
        a = argv[i]
        if a == "--offsets":
            opts["offsets"] = [int(x) for x in argv[i+1].split(",") if x.strip()]
            i += 2
        elif a == "--keywords":
            opts["keywords"] = [x for x in argv[i+1].split(",") if x.strip()]
            i += 2
        elif a == "--window":
            opts["window"] = int(argv[i+1]); i += 2
        elif a == "--max_windows":
            opts["max_windows"] = int(argv[i+1]); i += 2
        else:
            opts.setdefault("pos", []).append(a)
            i += 1
    return opts

def split_paras(text):
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

def main():
    argv = sys.argv
    if len(argv) < 3:
        print("用法: extract_windows.py <作品> <输出> [--offsets ...] [--keywords ...] [--window N] [--max_windows N]")
        sys.exit(1)
    src, dst = argv[1], argv[2]
    opts = parse_args(argv[3:])
    text = Path(src).read_text(encoding="utf-8")
    paras = split_paras(text)

    # 收集目标锚点:先按偏移(段起始),再加关键词命中段
    anchors = set(opts["offsets"])
    kw_matches = []
    if opts["keywords"]:
        kw_re = re.compile("|".join(opts["keywords"]))
        for p, off in paras:
            if kw_re.search(p) and len(p) > 40:
                kw_matches.append((off, p))
        # 按关键词密度排序取顶
        scored = [(sum(1 for k in opts["keywords"] if k in p), off, p) for off, p in kw_matches]
        scored.sort(key=lambda x: (-x[0], -len(x[2])))
        for _, off, _ in scored[: opts["max_windows"]]:
            anchors.add(off)

    anchors = sorted(anchors)
    if not anchors:
        print("无锚点")
        return

    # 扩窗:围绕每个锚点取 ±window 字符,折叠重叠窗口
    W = opts["window"]
    windows = []
    for off in anchors:
        lo = max(0, off - W)
        hi = min(len(text), off + W)
        windows.append((lo, hi))
    # 合并重叠/相邻窗口
    merged = []
    for lo, hi in sorted(windows):
        if merged and lo - merged[-1][1] < W * 0.5:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))

    out = []
    out.append(f"# {Path(src).name} 提取窗口 {len(merged)} 个,总字数 {sum(h-l for l,h in merged)}\n")
    for idx, (lo, hi) in enumerate(merged):
        seg = text[lo:hi]
        out.append(f"\n===== 窗口 {idx+1} (offset {lo}..{hi}) =====")
        out.append(seg)
    Path(dst).write_text("\n".join(out), encoding="utf-8")
    print(f"写 {dst}: {len(merged)} 窗口, {sum(h-l for l,h in merged)} 字")

if __name__ == "__main__":
    main()
