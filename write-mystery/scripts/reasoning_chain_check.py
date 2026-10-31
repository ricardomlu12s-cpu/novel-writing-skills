#!/usr/bin/env python3
"""推理链检查 — 结论必须由可见线索+真实知识推出,防跳步/防开天眼。

用法:
  python3 reasoning_chain_check.py <结论.txt> <线索文件.jsonl> <知识文件.jsonl>

线索文件: {"id","desc","status","seen_by"}  (status: 隐藏/部分公开/已公开)
知识文件: {"id","fact","domain","valid"}   (domain: 生/心/社/哲)
"""
import sys, json
from pathlib import Path

def load_jsonl(path):
    if not Path(path).exists():
        return []
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out

def main():
    if len(sys.argv) < 4:
        print("用法: reasoning_chain_check.py <结论.txt> <线索文件.jsonl> <知识文件.jsonl>")
        sys.exit(1)
    conclusion = Path(sys.argv[1]).read_text(encoding="utf-8")
    clues = load_jsonl(sys.argv[2])
    knowledge = load_jsonl(sys.argv[3])

    print(f"结论: {conclusion[:60]}...")
    print(f"线索数: {len(clues)} | 知识数: {len(knowledge)}")
    issues = []

    # 1. 结论是否引用了线索(简单检测:结论文本含线索关键词)
    clue_hits = [c for c in clues if c.get("desc","")[:6] in conclusion or any(w in conclusion for w in c.get("keywords",[]))]
    if not clue_hits:
        issues.append("断链: 结论未引用任何已知线索(可能跳步/开天眼)")
    else:
        hidden = [c for c in clue_hits if c.get("status") == "隐藏"]
        if hidden:
            issues.append(f"断链: 结论用了隐藏线索 {[h['id'] for h in hidden]}(主角当时看不到)")
        for c in clue_hits:
            print(f"  线索 {c.get('id')}: {c.get('desc','')} (状态:{c.get('status')}, seen_by:{c.get('seen_by','')})")

    # 2. 知识有效性(简单检测:用了标记无效的知识)
    invalid_k = [k for k in knowledge if k.get("valid") is False]
    if invalid_k:
        issues.append(f"断链: 用了无效知识 {[k['id'] for k in invalid_k]}(知识不真实)")

    if issues:
        print("\n 推理链检查:")
        for i in issues:
            print(f"  - {i}")
        print("→ 需补推理链(加可见线索支撑/换真实知识)")
    else:
        print("\n 推理链完整:结论由可见线索 + 真实知识推出")

if __name__ == "__main__":
    main()
