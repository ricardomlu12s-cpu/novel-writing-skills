#!/usr/bin/env python3
"""cadence_calc.py — 节律判定引擎(evolve-style)
读项目篇幅/结构/信号,判定"现在该不该学、学哪层、为什么"。
用法:
  python3 cadence_calc.py <项目目录> [--ch 当前章]
  未传 --ch 时,自动从 manuscripts/ 文件数推断当前进度。
"""
import json
import os
import re
import sys

# 篇幅档位表(与 SKILL.md / references/cadence-engine.md 一致)
BANDS = [
    # (档位, 上限章数, 小间隔分母, 中间隔分母, 小间隔下限, 中间隔下限)
    ("短篇",   40, 12, 4, 3, 10),
    ("中篇",  100, 12, 5, 4, 12),
    ("长篇",  300, 12, 6, 6, 20),
    ("超长篇", 10**9, 12, 7, 8, 30),
]

NONE = object()


def parse_int(value, default=NONE):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def estimate_n(proj):
    """估算预计总章数 N(取上推/外推孰高,优雅降级)。"""
    estimates = []

    # 外推:已写章数 / 细纲覆盖率(卷级细纲按每卷10章估算总计划,防覆盖率=1误判)
    written = 0
    mdir = os.path.join(proj, "manuscripts")
    if os.path.isdir(mdir):
        written = sum(1 for f in os.listdir(mdir)
                      if re.match(r"^ch\d{3}\.md$", f))
    outlines_dir = os.path.join(proj, "chapter-outlines")
    outline_files = sorted(
        f for f in os.listdir(outlines_dir) if f.endswith(".md")
    ) if os.path.isdir(outlines_dir) else []
    # 卷级细纲:按"卷"计数,假设每卷10章
    vol_chapters_guess = 10
    planned = len(outline_files) * vol_chapters_guess
    if outline_files and written:
        # 覆盖率 = 已写 / 计划(封顶0.5,防单一卷未闭合时误判覆盖率=1)
        coverage = min(0.5, written / max(planned, 1))
        est = written / coverage if coverage > 0 else written
        estimates.append(est)

    # 上推:卷弧数 × 每弧预计章数
    if outline_files:
        estimates.append(len(outline_files) * vol_chapters_guess)

    if estimates:
        return int(max(estimates))
    if written:
        return written * 2  # 兜底:假设还有一倍
    return 40  # 无数据:默认中篇初值


def band_for(n):
    for name, upper, _, _, _, _ in BANDS:
        if n <= upper:
            return name, upper
    return BANDS[-1][0], BANDS[-1][1]


def intervals_for(n):
    for name, upper, small_den, mid_den, small_min, mid_min in BANDS:
        if n <= upper:
            return (max(small_min, n // small_den),
                    max(mid_min, n // mid_den))
    return None


def read_cadence(proj):
    path = os.path.join(proj, "cadence.jsonl")
    entries = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def scan_detected_signal(proj, ch, cadence):
    """信号扫描:风格漂移 / AI味 / 同类问题 / 读者C级 / 注入失效。
    返回 (是否触发, 信号名, 建议层级)。数据缺失时返回 False(优雅降级)。

    注(2026-08-13 修复):lessons 路径曾在文档写 `.omc/story/<项目>/lessons.md`,
    但项目实际是 `lessons/lessons.md`(目录),导致读不到文件、信号扫描静默失效。
    此处同时兼容两种路径。
    """
    candidates = [os.path.join(proj, "lessons", "lessons.md"),
                  os.path.join(proj, "lessons.md")]
    lessons_path = next((p for p in candidates if os.path.isfile(p)), None)
    if not lessons_path:
        return False, None, None

    with open(lessons_path, encoding="utf-8") as fh:
        text = fh.read()

    # 连续 N 章重犯旧错(Stop 标记次数推断注入失效)——简单启发式。
    # lessons.md 实际格式为 `**Stop·...**` / `**Keep·...**`,故数 Stop 而非"避坑"。
    stop_markers = len(re.findall(r"\*\*Stop·", text))
    if stop_markers >= 6:
        return True, "lessons_injection_stale", "L3"

    return False, None, None


def append_check(proj, ch, triggers, level, n_est):
    """append-only 幂等登记:同 ch 已登记则不重复写(防 hook 重复触发污染账本)。
    返回 (是否新增, 原因)。"""
    path = os.path.join(proj, "cadence.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    entries = read_cadence(proj)
    # 幂等:若该章已有任何登记(type=check 或 learn),跳过
    for e in entries:
        if e.get("ch") == ch and e.get("type") in ("check", "learn"):
            return False, "already_logged"
    rec = {"ch": ch, "type": "learn" if triggers else "check",
           "level": level if triggers else None,
           "trigger": ",".join(triggers) if triggers else "interval",
           "n_est": n_est, "ts": "auto"}
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return True, "appended"


def main():
    if len(sys.argv) < 2:
        print("用法: cadence_calc.py <项目目录> [--ch 当前章] [--append]")
        sys.exit(1)
    proj = os.path.abspath(sys.argv[1])
    ch = parse_int(sys.argv[sys.argv.index("--ch") + 1]) if "--ch" in sys.argv else None
    do_append = "--append" in sys.argv
    silent = "--silent" in sys.argv

    # 当前章推断
    if ch is None:
        mdir = os.path.join(proj, "manuscripts")
        ch = sum(1 for f in os.listdir(mdir)
                 if re.match(r"^ch\d{3}\.md$", f)) if os.path.isdir(mdir) else 0
        # 章节从1开始:有 N 个文件 → 当前进度第 N 章
        ch = max(ch, 0)

    n_est = estimate_n(proj)
    band, _ = band_for(n_est)
    small_i, mid_i = intervals_for(n_est)
    cadence = read_cadence(proj)

    # 最近一次学习
    last_learn = None
    for e in reversed(cadence):
        if e.get("type") == "learn" and e.get("level"):
            last_learn = e
            break
    last_learn_ch = last_learn.get("ch", 0) if last_learn else 0
    last_learn_level = last_learn.get("level") if last_learn else None

    # 触发判定(优先级:结构锚点 > 信号 > 间隔)
    triggers = []
    level = None

    # 维度二:结构锚点(优先于一切)
    outlines_dir = os.path.join(proj, "chapter-outlines")
    arc_closed = False
    if os.path.isdir(outlines_dir):
        for f in os.listdir(outlines_dir):
            m = re.match(r"^卷([一二三四五六七八九十\d]+)[-_]", f)
            if not m:
                continue
            full = os.path.join(outlines_dir, f)
            try:
                with open(full, encoding="utf-8") as fh:
                    content = fh.read()
            except OSError:
                continue
            # 弧边界标记:细纲文件内"第N章"序号段出现即视为该卷边界接近
            # 简单启发式:文件内含"本卷完/卷终/收束" → 该卷已闭合
            if re.search(r"卷终|本卷完|卷尾|收束", content):
                arc_closed = True
    if arc_closed:
        triggers.append("arc_closed")
        level = "L3"

    # 维度三:信号
    sig_hit, sig_name, sig_level = scan_detected_signal(proj, ch, cadence)
    if sig_hit:
        triggers.append(sig_name)
        level = sig_level or level

    # 维度一:间隔兜底
    if not triggers:
        if ch >= small_i and (last_learn_ch == 0 or ch - last_learn_ch >= small_i):
            triggers.append("small_interval")
            level = "L2"
        if ch >= mid_i and (last_learn_ch == 0 or ch - last_learn_ch >= mid_i):
            triggers.append("mid_interval")
            level = "L3"

    # 卷边界 → 大学习(结构锚点最优先)
    if arc_closed:
        level = "L4"

    if silent:
        # 静默模式:仅登记,判触发与否(供 hook 判断)
        if do_append:
            ok, reason = append_check(proj, ch, triggers, level, n_est)
        if triggers:
            print("触发学习")
        return

    print(f"项目: {proj}")
    print(f"当前进度: 第 {ch} 章")
    print(f"估算总长 N: {n_est} 章 → {band}档")
    print(f"间隔: 小学习 {small_i} 章 | 中学习 {mid_i} 章")
    print(f"最近一次学习: 第 {last_learn_ch} 章 (层级 {last_learn_level})")
    if triggers:
        print(f"▶ 触发学习: {level} 层")
        print(f"  触发原因: {', '.join(triggers)}")
    else:
        print("▶ 未触发,登记已检查")
        print("  下次: 结构锚点(弧/卷闭合) 或 间隔到期")
    if do_append:
        ok, reason = append_check(proj, ch, triggers, level, n_est)
        print(f"[append] {'已登记' if ok else '跳过(幂等):' + reason}")


if __name__ == "__main__":
    main()
