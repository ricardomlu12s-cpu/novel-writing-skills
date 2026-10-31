#!/usr/bin/env python3
"""骨架遗忘 — 把正文/拆书产物提炼成"去细节骨架",供跨域重组。

本脚本做确定性抽取: 从文本里抽"身份/欲望/障碍/转变"四类结构信号,组合成骨架句。

用法:
  python3 skeleton_forget.py <文件.md|目录> [--out 骨架库路径]
  python3 skeleton_forget.py --asset <作品名>   # 对全局资产库的拆书产物做骨架化

产出: 骨架句(一行一个),存 ~/.omc/assets/plot/skeletons/ 或 --out 指定。
"""
import argparse
import re
import sys
from pathlib import Path

# 结构信号词(骨架 = 这些抽象结构的组合,而非具体人名/地名)
IDENTITY = ["孤儿", "遗孤", "转世", "重生", "身份", "身世", "血脉", "继承", "养子", "私生", "冒充"]
DESIRE = ["想要", "渴望", "追求", "复仇", "守护", "还债", "证明", "寻找", "夺回", "崛起", "登顶"]
OBSTACLE = ["宿敌", "仇敌", "诅咒", "绝症", "天劫", "强敌", "阴谋", "追杀", "封印", "束缚", "债"]
TRANSFORM = ["觉醒", "蜕变", "顿悟", "成长", "和解", "牺牲", "救赎", "选择", "代价", "黑化", "洗白", "超越"]

# 具体词过滤(去掉人名/地名/具体设定,只留抽象结构)。
# 通用策略: 删掉专有名词(连续中文2-4字 + 常见设定后缀),而非硬编码某部作品的人名。
PROPER_NOUN = re.compile(r"[一-鿿]{2,4}(?:学院|大陆|世界|宗门|家族|组织|帝国|王国|世家|圣地|秘境)")


def extract_signals(text):
    """从文本抽取四类结构信号的出现词。"""
    sig = {"identity": [], "desire": [], "obstacle": [], "transform": []}
    for cat, words in (("identity", IDENTITY), ("desire", DESIRE),
                       ("obstacle", OBSTACLE), ("transform", TRANSFORM)):
        for w in words:
            if w in text:
                sig[cat].append(w)
    return sig


def build_skeleton(sig):
    """四类信号组合成骨架句。缺的类用占位。"""
    parts = []
    if sig["identity"]:
        parts.append("身份" + "/".join(sig["identity"][:2]))
    else:
        parts.append("(身份)")
    if sig["desire"]:
        parts.append("欲望" + "/".join(sig["desire"][:2]))
    else:
        parts.append("(欲望)")
    if sig["obstacle"]:
        parts.append("障碍" + "/".join(sig["obstacle"][:2]))
    else:
        parts.append("(障碍)")
    if sig["transform"]:
        parts.append("转变" + "/".join(sig["transform"][:2]))
    else:
        parts.append("(转变)")
    return " → ".join(parts)


def process_text(text):
    """去具体名词 + 抽结构 → 骨架句。"""
    cleaned = PROPER_NOUN.sub("", text)
    sig = extract_signals(cleaned)
    return build_skeleton(sig)


def main():
    p = argparse.ArgumentParser(description="骨架遗忘")
    p.add_argument("target", nargs="?", help="文件或目录")
    p.add_argument("--asset", help="全局资产库里的作品名(替代 target)")
    p.add_argument("--out", help="输出骨架库路径(默认 ~/.omc/assets/plot/skeletons)")
    args = p.parse_args()

    if args.asset:
        target = Path.home() / ".omc" / "assets" / "deconstruction" / args.asset
    else:
        if not args.target:
            print("用法: skeleton_forget.py <文件.md|目录> [--out 路径]")
            sys.exit(2)
        target = Path(args.target).expanduser()

    # 收集文本
    texts = []
    if target.is_dir():
        for f in sorted(target.rglob("*.md")):
            texts.append(f.read_text(encoding="utf-8", errors="ignore"))
    elif target.is_file():
        texts.append(target.read_text(encoding="utf-8", errors="ignore"))
    else:
        print(f"目标不存在: {target}")
        sys.exit(1)

    # 每个文件产出一条骨架
    skeletons = []
    for t in texts:
        sk = process_text(t)
        if "(身份)" not in sk or "(欲望)" not in sk or "(障碍)" not in sk or "(转变)" not in sk:
            skeletons.append(sk)

    # 去重
    seen = []
    for sk in skeletons:
        if sk not in seen:
            seen.append(sk)

    if not seen:
        print("未抽到有效骨架(文本里结构信号太少)。")
        sys.exit(0)

    out_dir = Path(args.out) if args.out else (Path.home() / ".omc" / "assets" / "plot" / "skeletons")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "skeletons.txt"
    existing = set()
    if out_file.exists():
        existing = set(out_file.read_text(encoding="utf-8").splitlines())
    new_lines = [s for s in seen if s not in existing]
    with out_file.open("a", encoding="utf-8") as f:
        for s in new_lines:
            f.write(s + "\n")

    print(f"骨架遗忘: 抽出 {len(seen)} 条骨架(新增 {len(new_lines)})")
    print(f"骨架库: {out_file}\n")
    for s in seen[:10]:
        print(f"  {s}")
    if len(seen) > 10:
        print(f"  ... 共 {len(seen)} 条")


if __name__ == "__main__":
    main()
