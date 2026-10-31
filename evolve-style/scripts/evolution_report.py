#!/usr/bin/env python3
"""evolution_report.py — 进化学报告(evolve-style)
读 evolution/(实际指纹/作者指纹库/能力画像) + lessons + cadence,
生成 小/中/大 学习决策(偏差分类 + 能力画像 + 待练手法)。
用法:
  python3 evolution_report.py <项目目录> [--level L2|L3|L4|L5]
  未传 --level 时,读 cadence.jsonl 推断当前该学的层级。
"""
import json
import os
import re
import sys


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


def infer_level(proj):
    entries = read_cadence(proj)
    for e in reversed(entries):
        if e.get("level"):
            return e["level"]
    return "L2"


def read_lessons(proj):
    path = os.path.join(proj, "lessons.md")
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def summarize_lessons(text):
    """从 lessons.md 粗提取 有效/失效/待改进/避坑 行,供学习决策引用。"""
    summary = {"keep": [], "stop": [], "improve": [], "avoid": []}
    cur = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("###"):
            for k in summary:
                if k in line:
                    cur = k
                    break
            else:
                cur = None
            continue
        if cur and line.startswith("-"):
            summary[cur].append(line[1:].strip())
    # 只取最近各 3 条
    for k in summary:
        summary[k] = summary[k][-3:]
    return summary


def read_fingerprint_actual(proj):
    path = os.path.join(proj, "evolution", "fingerprint-actual.md")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    return ""


def read_capability(proj):
    path = os.path.join(proj, "evolution", "capability.md")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    return ""


def extract_pending(proj):
    """待练手法:从能力画像提取'待练'行,否则给默认白金手法清单。"""
    cap = read_capability(proj)
    pending = re.findall(r"待练[:：](.+)", cap)
    if pending:
        return [p.strip() for p in pending]
    return ["群像POV切换", "意识流心理", "冷笔触收尾"]


def main():
    if len(sys.argv) < 2:
        print("用法: evolution_report.py <项目目录> [--level L2|L3|L4|L5]")
        sys.exit(1)
    proj = os.path.abspath(sys.argv[1])
    level = None
    if "--level" in sys.argv:
        level = sys.argv[sys.argv.index("--level") + 1]
    if not level:
        level = infer_level(proj)

    lessons = read_lessons(proj)
    ls = summarize_lessons(lessons)
    pending = extract_pending(proj)
    fp_actual = read_fingerprint_actual(proj)

    print(f"项目: {proj}")
    print(f"学习层级: {level}")
    print()
    print("## lessons 摘要(学习决策引用)")
    print("有效(Keep):", ls["keep"] or "—")
    print("失效(Stop):", ls["stop"] or "—")
    print("待改进(Improve):", ls["improve"] or "—")
    print("避坑(Avoid):", ls["avoid"] or "—")
    print()
    print("## 能力画像")
    if fp_actual:
        print("实际指纹存在(evolution/fingerprint-actual.md): 已记录")
    else:
        print("实际指纹未记录 → 先跑 fingerprint_scan.py 生成")
    print("待练手法:", pending)
    print()
    print("## 学习决策")
    if level in ("L2",):
        print("▶ 情节学: 复盘本情节节奏/共鸣/手法, 定向注入下情节")
    elif level in ("L3", "L4"):
        print(f"▶ 弧段/卷学: 指纹对比(实际 vs 目标), 偏差三区分类")
        print("   - 锁死区(偏差≈0) → 主动去中心化(新手法/陌生化/限用令)")
        print("   - 健康区 → 个人化候选, 待作者确认升级")
        print("   - 失控区 → 拉回")
        print("▶ 能力画像更新: 手法掌握度 + 薄弱维度 + 待练手法")
        print("▶ 待练定向: 下卷注入 →", "、".join(pending))
    elif level == "L5":
        print("▶ 全书学: 风格史 + 能力成长曲线 + 作者指纹库定稿 → 反哺 style-library")
    else:
        print("未知层级:", level)

    if not lessons.strip():
        print()
        print("提示: lessons.md 不存在或为空 — 学习决策数据不足, 先补采集")


if __name__ == "__main__":
    main()
