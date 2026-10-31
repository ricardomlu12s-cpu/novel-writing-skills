#!/usr/bin/env python3
"""连续性确定性检查器 — 读正典账本/伏笔/关系,做无需 LLM 的硬扫描。

覆盖(全部确定性,不判主观质量):
  1. 承诺逾期     promises.jsonl  deadline_ch < 当前进度 且 status 未兑现
  2. 伏笔悬置过久 foreshadowing.jsonl  opened_ch 距今超过阈值 且 status=悬置
  3. 角色缺席     facts.jsonl known_by 统计,某角色超过阈值章未被提及
  4. 时间线单调   canon-ledger/timeline.md 章号是否乱序
  5. 关系突变     relationships.jsonl 同一 (a,b) 对 rel 反复翻转(列出,人工复核)
  6. 死亡候选     facts.jsonl 含"死/亡/阵亡/陨落"语义的角色(半自动,需人工复核)

用法:
  python3 continuity_check.py <项目目录> [--absent-threshold 10] [--foreshadow-threshold 20]

输出:按类型打印告警;无告警打印 。退出码 = 告警条数(0=全通过)。
"""
import json
import re
import sys
from pathlib import Path

FORESHADOW_STATUS_OK = {"开启", "悬置", "回收", "遗忘", "已埋钩", "已回收", "已兑现", "规划中", "已开启"}
PROMISE_OPEN = {"悬置", "在身", "拒绝", "未兑现", "进行中"}
DEATH_WORDS = ["死亡", "阵亡", "牺牲", "陨落", "已死", "死了", "被杀", "身死", "战死"]

CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def cn_to_int(s):
    s = s.strip()
    if not s:
        return None
    if "百" in s:
        a, _, b = s.partition("百")
        return (cn_to_int(a) or 1) * 100 + (cn_to_int(b) or 0)
    if "十" in s:
        a, _, b = s.partition("十")
        return (cn_to_int(a) or 1) * 10 + (cn_to_int(b) or 0)
    if s in CN_NUM:
        return CN_NUM[s]
    return None


def first_int(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value)
    m = re.search(r"\d+", s)
    if m:
        return int(m.group(0))
    m = re.search(r"卷([一二三四五六七八九十]+)", s)
    if m:
        return cn_to_int(m.group(1))
    return None


def chapter_no_from_name(name):
    m = re.match(r"^ch(\d{3})\.md$", name)
    return int(m.group(1)) if m else None


def current_progress(project):
    ms = project / "manuscripts"
    if not ms.is_dir():
        return 0
    nos = [chapter_no_from_name(f.name) for f in ms.glob("ch*.md")]
    return max([n for n in nos if n is not None], default=0)


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


def check_promises(project, progress, warnings):
    for p in load_jsonl(project / "canon-ledger" / "promises.jsonl"):
        status = p.get("status", "")
        if status not in PROMISE_OPEN:
            continue
        deadline = first_int(p.get("deadline_ch"))
        if deadline is not None and deadline < progress:
            warnings.append(
                f"[承诺逾期] ch{deadline} 已到仍未兑现: {p.get('promise','')} "
                f"(立誓 ch{p.get('made_ch','?')}, 状态={status})"
            )


def check_foreshadowing(project, progress, threshold, warnings):
    for f in load_jsonl(project / "foreshadowing.jsonl"):
        status = f.get("status", "")
        if status not in FORESHADOW_STATUS_OK:
            warnings.append(
                f"[伏笔状态异常] {f.get('id','?')} 状态={status!r} 非预期值: {f.get('desc','')}"
            )
        if status == "悬置":
            opened = first_int(f.get("opened_ch"))
            if opened is not None and progress - opened > threshold:
                warnings.append(
                    f"[伏笔悬置过久] {f.get('id','?')} 自 ch{opened} 开启已 {progress - opened} 章未回收: "
                    f"{f.get('desc','')}"
                )


def check_absent(project, progress, threshold, warnings):
    last_seen = {}
    for f in load_jsonl(project / "canon-ledger" / "facts.jsonl"):
        ch = first_int(f.get("ch"))
        if ch is None:
            continue
        for name in f.get("known_by", []):
            if name and (name not in last_seen or ch > last_seen[name]):
                last_seen[name] = ch
    for name, last in sorted(last_seen.items(), key=lambda kv: kv[1]):
        if progress - last > threshold:
            warnings.append(
                f"[角色缺席] {name} 自 ch{last} 起 {progress - last} 章未再被提及"
            )


def check_timeline(project, warnings):
    """timeline.md 章号是否单调。只匹配行首条目起始标记 `- (第X章...)`,
    行内"承接ch33/细纲ch38"等引用章号一律跳过。"""
    path = project / "canon-ledger" / "timeline.md"
    if not path.exists():
        return
    prev = 0
    entry_re = re.compile(r"^\s*-\s*\(第([一二三四五六七八九十百零]+)章")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = entry_re.match(line)
        if not m:
            continue
        n = cn_to_int(m.group(1))
        if n is None:
            continue
        if n < prev:
            warnings.append(f"[时间线乱序] 章号 {n} 出现在 {prev} 之后(行: {line.strip()})")
        prev = max(prev, n)


def check_relationship_flip(project, warnings):
    seq = {}
    for r in load_jsonl(project / "relationships.jsonl"):
        key = tuple(sorted([r.get("a", ""), r.get("b", "")]))
        if not key[0] or not key[1]:
            continue
        seq.setdefault(key, []).append((r.get("ch", "?"), r.get("rel", "")))
    for (a, b), changes in seq.items():
        rel_vals = [c[1] for c in changes]
        if len(set(rel_vals)) >= 3:
            warnings.append(
                f"[关系翻转] {a}×{b} 关系演变 {len(rel_vals)} 种: "
                + " → ".join(f"{c[1]}({c[0]})" for c in changes)
            )


def check_death_candidates(project, warnings):
    candidates = {}
    for f in load_jsonl(project / "canon-ledger" / "facts.jsonl"):
        fact = f.get("fact", "")
        if any(w in fact for w in DEATH_WORDS):
            for name in f.get("known_by", []):
                candidates.setdefault(name, []).append(fact[:60])
    for name, examples in candidates.items():
        if len(examples) >= 2:
            warnings.append(
                f"[死亡候选·待复核] {name} 相关 facts 含死亡语义 {len(examples)} 次,"
                f" 例: {examples[0]}…"
            )


def main():
    if len(sys.argv) < 2:
        print("用法: continuity_check.py <项目目录> [--absent-threshold 10] [--foreshadow-threshold 20]")
        sys.exit(2)
    project = Path(sys.argv[1])
    absent_th = 10
    fore_th = 20
    if "--absent-threshold" in sys.argv:
        absent_th = int(sys.argv[sys.argv.index("--absent-threshold") + 1])
    if "--foreshadow-threshold" in sys.argv:
        fore_th = int(sys.argv[sys.argv.index("--foreshadow-threshold") + 1])

    progress = current_progress(project)
    if progress == 0:
        print(f"未找到 manuscripts/ch*.md,进度=0(目录: {project})")
        sys.exit(2)

    warnings = []
    check_promises(project, progress, warnings)
    check_foreshadowing(project, progress, fore_th, warnings)
    check_absent(project, progress, absent_th, warnings)
    check_timeline(project, warnings)
    check_relationship_flip(project, warnings)
    check_death_candidates(project, warnings)

    print(f"连续性检查 @ 当前进度 ch{progress} (缺席阈值 {absent_th} 章, 伏笔阈值 {fore_th} 章)")
    print(f"{'=' * 60}")
    if not warnings:
        print(" 未发现连续性告警")
        sys.exit(0)
    for w in warnings:
        print(" " + w)
    print(f"{'=' * 60}")
    print(f"共 {len(warnings)} 条告警。注意: 缺席/悬置/死亡候选可能是作者有意,须人工复核,勿直接判错。")
    sys.exit(len(warnings))


if __name__ == "__main__":
    main()
