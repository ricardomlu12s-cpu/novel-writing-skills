#!/usr/bin/env python3
"""线索账本 — 登记/更新线索状态 + 公平竞赛复盘报告。

用法:
  python3 clue_ledger.py <项目目录> [--fair-play]

读 .omc/story/<项目>/clue-ledger.jsonl,
--fair-play 产出公平竞赛复盘(公开性核对 + 关键线索未公开告警)。
"""
import sys, json
from pathlib import Path

def load_clues(proj):
    path = proj / "clue-ledger.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out

def main():
    if len(sys.argv) < 2:
        print("用法: clue_ledger.py <项目目录> [--fair-play]")
        sys.exit(1)
    proj = Path(sys.argv[1])
    fair = "--fair-play" in sys.argv
    clues = load_clues(proj)

    if not clues:
        print("线索账本为空(未登记线索)")
        return

    print(f"=== 线索账本({len(clues)} 条) ===")
    by_status = {}
    for c in clues:
        st = c.get("status", "隐藏")
        by_status.setdefault(st, []).append(c)
        print(f"  {c.get('id')}: {c.get('desc','')[:30]} [{st}] seen_by:{c.get('seen_by','-')} 公开章:{c.get('revealed_ch','-')}")

    print(f"\n状态分布: " + ", ".join(f"{k}×{len(v)}" for k, v in by_status.items()))

    if fair:
        print("\n=== 公平竞赛复盘 ===")
        hidden = [c for c in clues if c.get("status") == "隐藏" and not c.get("is_red_herring")]
        if hidden:
            print(f" {len(hidden)} 条关键线索从未公开(可能开天眼):")
            for c in hidden:
                print(f"  - {c.get('id')}: {c.get('desc','')}(需补公开或交代隐藏)")
        else:
            print(" 无未公开的关键线索")
        red = [c for c in clues if c.get("is_red_herring")]
        print(f"伪线索(red herring): {len(red)} 条 {' 已标记' if red else '(无)'}")

if __name__ == "__main__":
    main()
