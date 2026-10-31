#!/usr/bin/env python3
"""资产库查重 + 检索 — 查某作品是否已拆过、按维度/标签检索资产。

用法:
  python3 asset_lookup.py <作品名|关键词>              # 查是否已拆过/已入库
  python3 asset_lookup.py --dimension 世界观 --tag 低魔  # 按维度+标签检索
  python3 asset_lookup.py --list                        # 列出全库资产

资产根: ~/.omc/assets/(可用环境变量 ASSET_ROOT 覆盖)
"""
import argparse
import json
import os
import sys
from pathlib import Path


def asset_root():
    return Path(os.environ.get("ASSET_ROOT", Path.home() / ".omc" / "assets"))


def load_asset_meta(root, sub):
    """读 deconstruction/<名>/asset.json 或 style/<名>/fingerprint.md 的标签。"""
    meta = {}
    p = root / sub
    if not p.exists():
        return meta
    aj = p / "asset.json"
    if aj.exists():
        try:
            meta = json.loads(aj.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    # style/technique/plot/knowledge 的标签在 md 顶部 frontmatter
    for md in p.glob("*.md"):
        txt = md.read_text(encoding="utf-8", errors="ignore")
        if txt.startswith("---"):
            end = txt.find("\n---", 4)
            if end > 0:
                for line in txt[4:end].splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k, v = k.strip(), v.strip().strip('"')
                        if k in ("source_book", "dimension", "granularity", "tags"):
                            if k == "tags":
                                meta[k] = [t.strip() for t in v.strip("[]").split(",")]
                            else:
                                meta[k] = v
    return meta


def scan(root):
    """扫描全库,返回 [(subpath, meta)]。"""
    out = []
    if not root.exists():
        return out
    for cat in ("deconstruction", "style", "technique", "plot", "knowledge"):
        cat_dir = root / cat
        if not cat_dir.is_dir():
            continue
        for sub in cat_dir.iterdir():
            if sub.is_dir():
                meta = load_asset_meta(root, f"{cat}/{sub.name}")
                meta.setdefault("_path", f"{cat}/{sub.name}")
                out.append(meta)
    return out


def main():
    p = argparse.ArgumentParser(description="资产库查重/检索")
    p.add_argument("keyword", nargs="?", help="作品名/关键词")
    p.add_argument("--dimension", help="按维度筛")
    p.add_argument("--tag", help="按标签筛")
    p.add_argument("--list", action="store_true", help="列出全库")
    args = p.parse_args()

    root = asset_root()
    assets = scan(root)

    if not assets:
        print(f"资产库为空(或不存在): {root}")
        print("首次使用: 拆书后产物放 deconstruction/<作品名>/,或迁移现有风格库。")
        sys.exit(0)

    if args.list:
        print(f"资产库({root})\n{'=' * 50}")
        for m in assets:
            print(f"  [{m.get('_path')}] {m.get('source_book','?')} | {m.get('dimension','?')} | {m.get('granularity','?')}")
        sys.exit(0)

    # 过滤
    result = assets
    if args.dimension:
        result = [m for m in result if m.get("dimension") == args.dimension]
    if args.tag:
        result = [m for m in result if args.tag in (m.get("tags") or [])]
    if args.keyword:
        kw = args.keyword
        result = [m for m in result if kw in (m.get("source_book", "") or "") or kw in (m.get("_path", ""))]

    if not result:
        print(f"未找到匹配资产: {args.keyword or ''} {args.dimension or ''} {args.tag or ''}")
        print("→ 可拆书后入库(deconstruction/<作品名>/),避免下次重复拆。")
        sys.exit(1)

    print(f"匹配 {len(result)} 件资产\n{'=' * 50}")
    for m in result:
        print(f"  {m.get('source_book','?')} [{m.get('dimension','?')}] 粒度={m.get('granularity','?')} tags={m.get('tags')}")
        print(f"     路径: {m.get('_path')}")
    # 命中即提示"可复用,不必重拆"
    if args.keyword and any(m.get("dimension") in ("世界观", "角色") for m in result):
        print("\n 该作品已有拆书产物,可直接引用(asset-refs.json),不必重复拆书烧 token。")


if __name__ == "__main__":
    main()
