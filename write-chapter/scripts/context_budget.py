#!/usr/bin/env python3
"""上下文预算估算器 — 把 token-budget-guard 的"预计下章注入量"变成确定性计算。

补 token-budget-guard 的盲区: 它说"注入量固定、可估算",但从没给估算工具。
本脚本读项目磁盘真实文件,算出下一章写前会注入哪些上下文、各多少字符/token,
一眼看出 token 花在哪、哪层摘要最占、是否该触发"开新会话"询问。

用法:
  python3 context_budget.py estimate <项目目录>          # 估算下一章注入量
  python3 context_budget.py estimate <项目目录> --ch 88  # 指定写到第几章(默认=当前+1)

估算口径(与 write-chapter 分层摘要规则一致):
  L5 全书 + 当前卷 L4 + 当前弧 L3 + 最近区块 L2 (空层自动跳过)
  + 活跃实体(角色卡/伏笔/关系) + 最近 3 条 lessons + RAG 回读(≤3段×500字)

输出: 每项文件名 + 字符数 + 折算 token(中文≈1字≈1~1.5 token,取 1.5 上界)。
"""
import re
import sys
from pathlib import Path

CHARS_PER_TOKEN = 1.5  # 中文保守上界


def chapter_no_from_name(name):
    m = re.match(r"^ch(\d{3})\.md$", name)
    return int(m.group(1)) if m else None


def size_of(path):
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8"))


def file_entry(label, path, items):
    """登记一个文件项,返回 (label, path, chars)。"""
    c = size_of(path)
    items.append((label, str(path), c))
    return c


def current_progress(project):
    ms = project / "manuscripts"
    if not ms.is_dir():
        return 0
    nos = [chapter_no_from_name(f.name) for f in ms.glob("ch*.md")]
    return max([n for n in nos if n is not None], default=0)


def estimate(project, target_ch):
    items = []  # (label, path, chars)
    s = project / "summaries"

    # 分层摘要(空层跳过)
    l5 = s / "L5" / "novel.md"
    if l5.exists():
        file_entry("L5全书摘要", l5, items)

    # 当前卷 L4: 取卷号最大的文件
    l4_dir = s / "L4"
    if l4_dir.is_dir():
        vols = sorted(l4_dir.glob("*.md"))
        if vols:
            file_entry("L4当前卷摘要", vols[-1], items)

    # 当前弧 L3: 取文件名 arc 号最大的
    l3_dir = s / "L3"
    if l3_dir.is_dir():
        arcs = sorted(l3_dir.glob("*.md"))
        if arcs:
            file_entry("L3当前弧摘要", arcs[-1], items)

    # 最近区块 L2: 若存在
    l2_dir = s / "L2"
    if l2_dir.is_dir():
        blocks = sorted(l2_dir.glob("*.md"))
        if blocks:
            file_entry("L2最近区块摘要", blocks[-1], items)

    # 活跃实体
    proj_files = {
        "角色卡(characters/)": None,
        "伏笔(foreshadowing.jsonl)": project / "foreshadowing.jsonl",
        "关系(relationships.jsonl)": project / "relationships.jsonl",
        "承诺(promises.jsonl)": project / "canon-ledger" / "promises.jsonl",
        "POV边界(pov-boundary.jsonl)": project / "pov-boundary.jsonl",
    }
    for label, p in proj_files.items():
        if p is not None:
            file_entry(label, p, items)

    # 角色卡目录合计(写章前会读活跃角色卡)
    ch_dir = project / "characters"
    if ch_dir.is_dir():
        chars_total = sum(size_of(f) for f in ch_dir.glob("*.md"))
        if chars_total:
            items.append(("角色卡合计", str(ch_dir), chars_total))

    # 最近 3 条 lessons(lessons/lessons.md)
    lessons = project / "lessons" / "lessons.md"
    if lessons.exists():
        # 粗略: 取 lessons 末尾 ~1500 字符代表"最近3条"
        txt = lessons.read_text(encoding="utf-8")
        tail = txt[-1500:]
        items.append(("lessons(最近3条,估算)", str(lessons), len(tail)))

    # RAG 回读(≤3段×500字,上界)
    rag = 3 * 500
    items.append(("RAG回读(上界3段×500字)", "(估算)", rag))

    return items


def main():
    if len(sys.argv) < 2:
        print("用法: context_budget.py estimate <项目目录> [--ch N]")
        print("      context_budget.py gate <项目目录> [--max-tok 40000]   # 写章前强制门禁")
        sys.exit(2)
    cmd = sys.argv[1]
    if cmd not in ("estimate", "gate"):
        print("未知命令,支持 estimate / gate")
        sys.exit(2)
    project = Path(sys.argv[2])
    target_ch = current_progress(project) + 1
    if "--ch" in sys.argv:
        target_ch = int(sys.argv[sys.argv.index("--ch") + 1])

    items = estimate(project, target_ch)

    if cmd == "gate":
        max_tok = 40000
        if "--max-tok" in sys.argv:
            max_tok = int(sys.argv[sys.argv.index("--max-tok") + 1])
        gate(project, target_ch, items, max_tok)
        return

    print(f"下一章 ch{target_ch} 上下文注入估算\n" + "=" * 60)
    total_chars = 0
    for label, path, chars in items:
        total_chars += chars
        if chars == 0:
            continue
        tok = chars / CHARS_PER_TOKEN
        print(f"  {label:<28} {chars:>7} 字 ≈ {tok:>7.0f} token")
        print(f"      {path}")

    print("=" * 60)
    total_tok = total_chars / CHARS_PER_TOKEN
    print(f"合计: {total_chars} 字 ≈ {total_tok:.0f} token (中文按 {CHARS_PER_TOKEN} 字/token 上界)")

    # 阈值提示(对齐 token-budget-guard 的 200k 窗 70% 阈值)
    if total_tok > 140000:
        print("\n 预计注入量已超 200k 窗的 70%(140k),强烈建议开新会话续写。")
    elif total_tok > 80000:
        print("\n 注入量偏高,注意本会话累计上下文,接近阈值时开新会话。")
    else:
        print("\n 注入量健康,单章成本可控。")


def gate(project, target_ch, items, max_tok):
    """写章前强制门禁: 注入量超标 → 强制最小装配,不超标才放行。"""
    total_chars = sum(c for _, _, c in items)
    total_tok = total_chars / CHARS_PER_TOKEN

    print(f"写章前门禁 @ ch{target_ch}\n" + "=" * 60)
    print(f"当前注入量: {total_chars} 字 ≈ {total_tok:.0f} token (上限 {max_tok})")

    # 找出最大头(通常是角色卡)
    if items:
        biggest = max(items, key=lambda x: x[2])
        label, path, chars = biggest
        if chars > 0:
            print(f"最大头: {label} ({chars} 字 ≈ {chars / CHARS_PER_TOKEN:.0f} token)")

    if total_tok <= max_tok:
        print("\n 门禁通过: 注入量在预算内,可写章。")
        sys.exit(0)

    # 超标 → 强制最小装配
    print(f"\n 门禁拦截: 注入量超上限 {total_tok:.0f} > {max_tok}。")
    print("最小上下文装配(必须执行,替代全量注入):")
    print("  1. 角色卡 → 用 lorebook 按场景关键词检索,只注入命中块:")
    print(f"     python3 ~/.claude/skills/build-world/scripts/lorebook.py inject {project} --query \"<本场景关键词>\" --top 5")
    print("  2. 分层摘要 → 只注入 L5(若有)+当前卷L4+当前弧L3,跳过 L2/L1")
    print("  3. lessons → 只注入最近 1 条有证据的,不是 3 条")
    print("  4. RAG 回读 → 降到 ≤2 段")
    print("\n装配后重跑: context_budget.py gate <项目> --max-tok <值> 确认达标。")
    sys.exit(1)


if __name__ == "__main__":
    main()
