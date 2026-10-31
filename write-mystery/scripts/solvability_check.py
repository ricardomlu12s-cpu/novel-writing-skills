#!/usr/bin/env python3
"""可解性事前评判 — 补 fair-play-check 的盲区。

fair-play-check 做"结尾复盘"(事后看线索公开过没),本脚本做"事前可解性":
  在解谜/反转发生的第 N 章,读者(或主角)当时是否已拿到足够线索?

确定性检查(无需 LLM):
  1. 线索公开时序: 每条关键线索 revealed_ch vs 解谜章 N
     - 关键线索在 N 之后才公开 → 当时读者无法解出 = 公平性风险(开天眼)
     - 除非该线索被显式"隐藏且有交代"(held_back=true),否则计入"事后公开"告警
  2. 可解性评分: (N 时已公开的关键线索数) / (关键线索总数)
  3. 可信度三态: 每条线索/conclusion 标注 confirmed/suspected/disproven,
     检查"结论"若标 confirmed 但依赖线索仍 suspected → 置信度与证据不匹配

用法:
  python3 solvability_check.py <项目目录> --solve-ch 45   # 第45章解谜
  python3 solvability_check.py <项目目录> --solve-ch 45 --min-solvable 0.6

数据源: .omc/story/<项目>/clue-ledger.jsonl
  线索字段: id, desc, status(隐藏/部分公开/已公开), revealed_ch, is_red_herring, held_back
  结论字段: id, conclusion, depends_on[], credibility(confirmed/suspected/disproven)
"""
import argparse
import json
import sys
from pathlib import Path

CRED_STATES = {"confirmed", "suspected", "disproven"}


def load_jsonl(path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def first_int(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v)
    import re
    m = re.search(r"\d+", str(v))
    return int(m.group(0)) if m else None


def load_clues(proj):
    clues = load_jsonl(proj / "clue-ledger.jsonl")
    # 兼容: 结论也可能混在同一个 jsonl 里(带 depends_on/credibility 字段)
    return [c for c in clues if "desc" in c or "id" in c]


def main():
    p = argparse.ArgumentParser(description="可解性事前评判")
    p.add_argument("project", help="项目目录")
    p.add_argument("--solve-ch", type=int, required=True, help="解谜/反转发生的章号")
    p.add_argument("--min-solvable", type=float, default=0.6, help="可解性下限(默认0.6)")
    args = p.parse_args()

    proj = Path(args.project)
    rows = load_jsonl(proj / "clue-ledger.jsonl")

    clues = [r for r in rows if r.get("desc") or r.get("status")]
    conclusions = [r for r in rows if r.get("conclusion") or r.get("depends_on")]

    if not clues and not conclusions:
        print(f"clue-ledger.jsonl 为空或不存在: {proj / 'clue-ledger.jsonl'}")
        print("(本项目非智斗题材,无智斗线索账本——脚本可用但无数据)")
        sys.exit(0)

    print(f"可解性评判 @ 解谜章 ch{args.solve_ch}\n" + "=" * 60)

    warnings = []
    key_clues = [c for c in clues if not c.get("is_red_herring")]
    revealed_before = []
    revealed_after = []

    for c in key_clues:
        rc = first_int(c.get("revealed_ch"))
        st = c.get("status", "隐藏")
        if st == "已公开" or (rc is not None and rc <= args.solve_ch):
            revealed_before.append(c)
        else:
            # 未在解谜前公开
            if c.get("held_back"):
                revealed_before.append(c)  # 显式隐藏且有交代,视为"可用"
            else:
                revealed_after.append(c)

    total = len(key_clues)
    solvable_ratio = len(revealed_before) / total if total else 1.0

    print(f"关键线索 {total} 条 | 解谜前已公开/可用 {len(revealed_before)} 条 | "
          f"事后才公开 {len(revealed_after)} 条")
    print(f"可解性评分: {solvable_ratio:.0%}  (下限 {args.min_solvable:.0%})")

    for c in revealed_after:
        warnings.append(
            f"[事后公开] {c.get('id','?')}: {c.get('desc','')[:40]} "
            f"在 ch{first_int(c.get('revealed_ch')) or '?'} 才公开,解谜 ch{args.solve_ch} 时读者无法拿到 = 公平性风险"
        )

    if solvable_ratio < args.min_solvable:
        warnings.append(
            f"[不可解] 可解性 {solvable_ratio:.0%} 低于下限 {args.min_solvable:.0%}: "
            f"解谜时关键线索公开不足,读者无法独立解出(可能开天眼/硬推)"
        )

    # 可信度三态检查
    if conclusions:
        print("\n结论可信度三态检查:")
        clue_cred = {}
        for c in clues:
            clue_cred[c.get("id")] = c.get("credibility", "confirmed")
        for con in conclusions:
            cred = con.get("credibility", "confirmed")
            if cred not in CRED_STATES:
                warnings.append(f"[可信度] {con.get('id','?')} 置信度={cred!r} 非三态(confirmed/suspected/disproven)")
                continue
            deps = con.get("depends_on", [])
            dep_creds = [clue_cred.get(d, "confirmed") for d in deps]
            # confirmed 结论不能依赖 disproven 线索
            if cred == "confirmed" and "disproven" in dep_creds:
                warnings.append(
                    f"[可信度矛盾] 结论 {con.get('id','?')} 标 confirmed 但依赖被证伪的线索 {deps} → 置信度与证据不匹配"
                )
            if cred == "confirmed" and "suspected" in dep_creds:
                warnings.append(
                    f"[可信度存疑] 结论 {con.get('id','?')} 标 confirmed 但依赖线索仍 suspected {deps} → 建议降为 suspected"
                )
            print(f"  {con.get('id','?')}: {con.get('conclusion','')[:40]} [{cred}] 依赖 {deps}")

    print("=" * 60)
    if not warnings:
        print(" 可解性达标,线索公开时序合理")
        sys.exit(0)
    for w in warnings:
        print(" " + w)
    print(f"\n共 {len(warnings)} 条公平性/可解性告警。")
    sys.exit(len(warnings))


if __name__ == "__main__":
    main()
