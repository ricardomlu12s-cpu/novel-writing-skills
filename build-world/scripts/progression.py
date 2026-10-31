#!/usr/bin/env python3
"""设定版本演化(Progressions) — 从 append-only 的关系账本重建"当前态 + 演变时间线"。

  翻原始 jsonl 看不到"现在的状态"和"怎么一步步变成这样的"。
  本脚本把同一 (a,b) 对的所有历史合并,输出:
    1. 当前态快照: 每对关系现在是什么(取 ch 最新一条)
    2. 演变时间线: 每对关系的完整变化链 a→b 在 chX 从「敌」变「友」
    3. 突变告警: 相邻两条 rel 变化无中间过渡(如 ch5 敌对 → ch6 挚友,无动机记录)

用法:
  python3 progression.py <项目目录> [--pair 路明非 绘梨衣]

数据源: .omc/story/<项目>/relationships.jsonl
"""
import argparse
import sys
from pathlib import Path

# 关系极性(用于突变检测: 敌对↔亲密 直接跳变算突变)
HOSTILE = {"敌对", "仇敌", "宿敌", "对立", "敌", "仇"}
FRIENDLY = {"挚友", "盟友", "结盟", "友", "恋爱", "夫妻", "CP", "守护", "共生", "亲人", "兄弟"}


def load_jsonl(path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(__import__("json").loads(line))
        except ValueError:
            continue
    return out


def polarity(rel):
    rel = str(rel)
    if any(h in rel for h in HOSTILE):
        return "敌对"
    if any(f in rel for f in FRIENDLY):
        return "亲密"
    return "中性"


def sort_key(ch):
    """关系里的 ch 可能是 '卷一'/'卷三(b006...)'/12 等,尽量提取可排序键。"""
    import re
    s = str(ch)
    m = re.search(r"\d+", s)
    if m:
        return (0, int(m.group(0)))
    m = re.search(r"卷([一二三四五六七八九十]+)", s)
    if m:
        cn = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
        n = cn.get(m.group(1), 0)
        return (1, n)
    return (2, 0)


def build_pairs(rows):
    pairs = {}
    for r in rows:
        a, b = r.get("a", ""), r.get("b", "")
        if not a or not b:
            continue
        key = tuple(sorted([a, b]))
        pairs.setdefault(key, []).append(r)
    for key in pairs:
        pairs[key].sort(key=lambda r: sort_key(r.get("ch", "")))
    return pairs


def main():
    p = argparse.ArgumentParser(description="设定版本演化(Progressions)")
    p.add_argument("project", help="项目目录")
    p.add_argument("--pair", nargs=2, metavar=("A", "B"), help="只看某一对关系")
    args = p.parse_args()

    proj = Path(args.project)
    rows = load_jsonl(proj / "relationships.jsonl")
    if not rows:
        print(f"relationships.jsonl 为空或不存在: {proj / 'relationships.jsonl'}")
        sys.exit(0)

    pairs = build_pairs(rows)

    if args.pair:
        key = tuple(sorted(args.pair))
        if key not in pairs:
            print(f"未找到关系对: {args.pair}")
            sys.exit(1)
        pairs = {key: pairs[key]}

    print(f"设定版本演化(Progressions) — 共 {len(pairs)} 对关系\n" + "=" * 60)

    warnings = []
    for (a, b), changes in pairs.items():
        current = changes[-1]
        cur_rel = current.get("rel", "")
        print(f"\n【{a} × {b}】 当前态: {cur_rel}  (最新 {current.get('ch','?')})")

        # 演变时间线
        for c in changes:
            print(f"    {c.get('ch','?')}: {c.get('rel','')}")

        # 突变检测: 相邻两条极性从敌对直接跳到亲密(无中性/过渡),且无 note
        for i in range(1, len(changes)):
            prev, cur = changes[i - 1], changes[i]
            p1, p2 = polarity(prev.get("rel", "")), polarity(cur.get("rel", ""))
            if p1 != p2 and p1 != "中性" and p2 != "中性" and not cur.get("note"):
                warnings.append(
                    f"[关系突变] {a}×{b}: {prev.get('ch')} {prev.get('rel')} → "
                    f"{cur.get('ch')} {cur.get('rel')} 无过渡动机(note 缺失)"
                )

    print("\n" + "=" * 60)
    if warnings:
        for w in warnings:
            print(" " + w)
        print(f"\n共 {len(warnings)} 条关系突变告警(可能缺动机交代)。")
    else:
        print(" 关系演变均有过渡或已记录动机,无突变。")
    sys.exit(len(warnings))


if __name__ == "__main__":
    main()
