#!/usr/bin/env python3
"""Lorebook 按需注入 — 把设定库按标题切成条目,写场景时只注入命中的块,不再全量读。

背景(2026-10-31 context_budget.py 实测发现): 写一章注入的"活跃实体"里,
角色卡合计 17104 字 ≈ 单章注入量的 60%,是隐性 token 大头。
本脚本把 world.md / power-system.md / locations.md / characters/*.md 按 ##/### 切成
独立条目,建关键词索引;写场景时按场景关键词只取命中块(默认 Top 8 块)。

用法:
  python3 lorebook.py build  <项目目录>          # 建条目索引
  python3 lorebook.py inject <项目目录> --query "楚子航 言灵 战斗" [--top 8]

索引位置: <项目目录>/.index/lorebook.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

INDEX_NAME = ".index"
LOREBOOK = "lorebook.json"
SETTINGS_FILES = ["world.md", "power-system.md", "locations.md"]

HEADING_RE = re.compile(r"^(#{2,3})\s+(.+)$")
CN_TOKEN = re.compile(r"[一-鿿]+|[A-Za-z0-9]+")


def tokenize(text):
    out = []
    for m in CN_TOKEN.findall(text.lower()):
        if re.match(r"[一-鿿]", m):
            out.extend(list(m))  # 中文单字
        else:
            out.append(m)
    return out


def split_blocks(text, source):
    """按 ##/### 标题切块,返回 [(heading_path, body)]。"""
    lines = text.splitlines()
    blocks = []
    cur_title = source
    cur_lines = []
    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            if cur_lines:
                blocks.append((cur_title, "\n".join(cur_lines)))
            cur_title = f"{source} > {m.group(2).strip()}"
            cur_lines = []
        else:
            cur_lines.append(line)
    if cur_lines:
        blocks.append((cur_title, "\n".join(cur_lines)))
    return blocks


def build(project):
    entries = []
    for fn in SETTINGS_FILES:
        f = project / fn
        if not f.exists():
            continue
        for title, body in split_blocks(f.read_text(encoding="utf-8"), fn):
            body = body.strip()
            if not body:
                continue
            entries.append({
                "title": title,
                "body": body,
                "chars": len(body),
                "tokens": tokenize(title + " " + body),
            })

    ch_dir = project / "characters"
    if ch_dir.is_dir():
        for f in sorted(ch_dir.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            for title, body in split_blocks(text, f"characters/{f.name}"):
                body = body.strip()
                if not body:
                    continue
                entries.append({
                    "title": title,
                    "body": body,
                    "chars": len(body),
                    "tokens": tokenize(title + " " + body),
                })

    idx_dir = project / INDEX_NAME
    idx_dir.mkdir(exist_ok=True)
    out_path = idx_dir / LOREBOOK
    # 索引里不存 tokens(太大),存 title+body 即可;检索时现算
    payload = [{"title": e["title"], "body": e["body"], "chars": e["chars"]} for e in entries]
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f" Lorebook 索引: {len(entries)} 条目")
    total = sum(e["chars"] for e in entries)
    print(f"   设定库总量 {total} 字 → 按需注入只取命中块(通常 < 1/3)")
    print(f"   索引文件: {out_path}")


def inject(project, query, top):
    idx_path = project / INDEX_NAME / LOREBOOK
    if not idx_path.exists():
        print("索引不存在,先 build: python3 lorebook.py build <项目目录>")
        sys.exit(1)
    entries = json.loads(idx_path.read_text(encoding="utf-8"))
    q_tokens = set(tokenize(query))

    scored = []
    for e in entries:
        e_tokens = tokenize(e["title"] + " " + e["body"])
        title_hit = sum(1 for t in q_tokens if t in tokenize(e["title"]))
        body_hit = sum(1 for t in q_tokens if t in e_tokens)
        # 标题命中权重高(标题是条目的语义标签)
        score = title_hit * 3 + body_hit
        if score > 0:
            scored.append((score, e))

    scored.sort(key=lambda x: x[0], reverse=True)
    picked = scored[:top]

    if not picked:
        print("无命中设定块。换场景关键词,或加 --top 更多。")
        return

    total_chars = 0
    print(f"Lorebook 按需注入 @ 查询「{query}」\n" + "=" * 60)
    for score, e in picked:
        total_chars += e["chars"]
        print(f"\n### {e['title']}  (命中分 {score}, {e['chars']} 字)")
        print(e["body"][:400])
        if len(e["body"]) > 400:
            print("   …")
    print("\n" + "=" * 60)
    print(f"注入 {len(picked)} 块, 共 {total_chars} 字 "
          f"(vs 全量 {sum(e['chars'] for e in entries)} 字, 省 {1 - total_chars / sum(e['chars'] for e in entries):.0%})")


def main():
    p = argparse.ArgumentParser(description="Lorebook 按需注入")
    sub = p.add_subparsers(dest="cmd", required=True)
    pb = sub.add_parser("build", help="建条目索引")
    pb.add_argument("project")
    pi = sub.add_parser("inject", help="按场景注入设定块")
    pi.add_argument("project")
    pi.add_argument("--query", required=True, help="场景关键词,如 战斗 言灵 楚子航")
    pi.add_argument("--top", type=int, default=8)
    args = p.parse_args()
    project = Path(args.project).expanduser()
    if args.cmd == "build":
        build(project)
    else:
        inject(project, args.query, top=args.top)


if __name__ == "__main__":
    main()
