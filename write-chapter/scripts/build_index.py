#!/usr/bin/env python3
"""正文检索索引 — 用 Python 内置 sqlite3 FTS5 对 manuscripts 建可查询索引。

替代原 omc-learned/novel-creator-skill/scripts/plot_rag_retriever.py 那条坏依赖:
  旧脚本硬编码 novel-creator 自己的目录(00_memory/character_tracker.md + 03_manuscript/),
  与本链 .omc/story/<项目>/manuscripts/ 结构对不上,参数也传不进。

本脚本零第三方依赖(仅标准库 sqlite3),中文按字切 n-gram 入库 FTS5,支持:
  build   — 建/重建索引(按 mtime 增量,改过的章才重建)
  search  — 检索,返回 Top-K 章 + 命中片段(带行号/原文)

用法:
  python3 build_index.py build  <项目目录>
  python3 build_index.py search <项目目录> "玉佩 刻痕" [--top 3]

索引位置: <项目目录>/.index/retrieval.db (可随时删,重建即可)
"""
import argparse
import re
import sqlite3
import sys
from pathlib import Path

INDEX_NAME = ".index"
DB_NAME = "retrieval.db"

CN_CHAR = re.compile(r"[一-鿿]")
CN_PUNCT = re.compile(r"[一-鿿][，。！？；：、（）《》「」『』　]+")


def chapter_no_from_name(name):
    m = re.match(r"^ch(\d{3})\.md$", name)
    return int(m.group(1)) if m else None


def tokenize(text):
    """中文按字切(单字 token)+ 英文/数字按词,供 FTS5 与查询共用。"""
    tokens = []
    for part in re.findall(r"[一-鿿]|[A-Za-z0-9]+", text.lower()):
        if re.match(r"[一-鿿]", part):
            tokens.extend(list(part))
        else:
            tokens.append(part)
    return tokens


def clean_for_search(text):
    """去掉中文标点粘连,保留字面。"""
    return CN_PUNCT.sub(lambda m: m.group(0)[0] + " " + m.group(0)[1:], text)


def ensure_db(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE IF NOT EXISTS chapters("
                 "no INTEGER PRIMARY KEY, file TEXT, mtime REAL)")
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS idx USING fts5("
                 "no UNINDEXED, content)")
    return conn


def build(project, incremental=True):
    ms = project / "manuscripts"
    if not ms.is_dir():
        print(f"未找到正文目录: {ms}")
        sys.exit(1)
    db_dir = project / INDEX_NAME
    db_dir.mkdir(exist_ok=True)
    conn = ensure_db(db_dir / DB_NAME)

    # 已有索引的 mtime
    existing = {row[0]: row[2] for row in conn.execute("SELECT no, file, mtime FROM chapters")}
    files = sorted(ms.glob("ch*.md"), key=lambda f: chapter_no_from_name(f.name) or 0)

    rebuilt = 0
    reused = 0
    for f in files:
        no = chapter_no_from_name(f.name)
        if no is None:
            continue
        mtime = f.stat().st_mtime
        if incremental and no in existing and abs(existing[no] - mtime) < 1e-6:
            reused += 1
            continue
        text = f.read_text(encoding="utf-8")
        tokens = tokenize(clean_for_search(text))
        content = " ".join(tokens)
        # 覆盖写: 删旧再插
        conn.execute("DELETE FROM chapters WHERE no=?", (no,))
        conn.execute("DELETE FROM idx WHERE no=?", (no,))
        conn.execute("INSERT INTO chapters(no, file, mtime) VALUES(?,?,?)",
                     (no, f.name, mtime))
        conn.execute("INSERT INTO idx(no, content) VALUES(?,?)", (no, content))
        rebuilt += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM chapters").fetchone()[0]
    print(f" 索引完成: 共 {total} 章(本次重建 {rebuilt}, 复用 {reused})")
    print(f"   索引文件: {db_dir / DB_NAME}")
    conn.close()


def _snippet_tokens(tokens, hits):
    """从 tokens 里取命中词附近窗口。"""
    if not hits:
        return []
    spans = []
    for i, t in enumerate(tokens):
        if t in hits:
            spans.append(i)
    # 取每个命中点 ±12 字窗口
    out = []
    for s in spans:
        lo, hi = max(0, s - 12), min(len(tokens), s + 12)
        out.append("".join(tokens[lo:hi]))
    return out[:5]


def search(project, query, top=3):
    db_path = project / INDEX_NAME / DB_NAME
    if not db_path.exists():
        print("索引不存在,先 build: python3 build_index.py build <项目目录>")
        sys.exit(1)
    conn = ensure_db(db_path)

    q_tokens = tokenize(query)
    if not q_tokens:
        print("查询为空或无可检索 token")
        sys.exit(1)
    # FTS5 查询: 各 token OR
    q = " OR ".join(f'"{t}"' for t in q_tokens)
    rows = conn.execute(
        "SELECT no, bm25(idx) AS score, snippet(idx, 1, '', '', '…', 24) AS snip "
        "FROM idx WHERE idx MATCH ? ORDER BY bm25(idx) LIMIT ?",
        (q, top),
    ).fetchall()

    if not rows:
        print("无匹配。可换关键词或先确认已 build。")
        conn.close()
        return

    print(f"查询: {query}  (Top {top})\n" + "=" * 60)
    for no, score, snip in rows:
        fname = f"ch{no:03d}.md"
        # snippet 返回的片段已用 … 分隔,转成可读
        frag = " … ".join(s for s in snip.split("…") if s.strip())
        print(f"ch{no:03d}  bm25={score:.2f}")
        print(f"   片段: {frag[:300]}")
        print()
    conn.close()


def main():
    p = argparse.ArgumentParser(description="正文 FTS5 检索索引")
    sub = p.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("build", help="建/增量更新索引")
    pb.add_argument("project", help="项目目录")
    pb.add_argument("--full", action="store_true", help="强制全量重建")

    ps = sub.add_parser("search", help="检索")
    ps.add_argument("project", help="项目目录")
    ps.add_argument("query", help="检索词")
    ps.add_argument("--top", type=int, default=3)

    args = p.parse_args()
    project = Path(args.project).expanduser()
    if args.cmd == "build":
        build(project, incremental=not args.full)
    else:
        search(project, args.query, top=args.top)


if __name__ == "__main__":
    main()
