#!/usr/bin/env python3
"""发布格式导出 — 把 manuscripts/ch*.md(每文件=一章)导出为"分卷文件夹→章txt"结构。

按轮增量 + 待整轮回检(防"未满轮提前发布",2026-08-05 事故教训):
- 未满一轮的新章导出时文件名带 "(待整轮回检)" 后缀,不进"正式发布";
- 满一轮且发布 txt 标点校验通过 → 自动剥离后缀转正式。

用法:
  python3 export_publish.py <项目目录> [--out 发布目录名] [--batch 批次大小]

输入:  <项目>/manuscripts/ch001.md  (每文件=一章,含 # 卷名 + ## 第X章 标题)
输出:  <项目>/<发布目录>/<卷名>/<第X章 标题>.txt
  - 卷名从 ch*.md 内第一个 "# 卷名" 提取(缺省回退文件名)
  - 章名从 "## 第X章 标题" 提取(中文数字转序)
  - 保留正文段落,章标题保留为正文首行,去掉其余 markdown 标题符号
  - 导出后自动对发布目录跑 check_punct_spec.py --all(强制,不过不出包)
"""
import re, sys, subprocess
from pathlib import Path

SUFFIX = "(待整轮回检)"
# 相对本脚本定位 sibling skill 的检查脚本,避免硬编码用户名/主目录(换机/换用户不崩)
CHECK_PUNCT = str(Path(__file__).resolve().parents[2] / "remove-ai-tone" / "scripts" / "check_punct_spec.py")

CN_NUM = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}
TITLE_RE = re.compile(r"^第([一二三四五六七八九十百零]+)章\s+(.+)$")
CH_FILE_RE = re.compile(r"^ch(\d{3})\.md$")

def cn_to_int(s):
    """中文数字→整数。支持 一~九十九、一百、一百零三、一百二十三。"""
    if not s:
        return 0
    if "百" in s:
        a, _, b = s.partition("百")
        return (cn_to_int(a) or 1) * 100 + cn_to_int(b)
    if "十" in s:
        a, _, b = s.partition("十")
        return (cn_to_int(a) or 1) * 10 + cn_to_int(b)
    total = 0
    for ch in s:
        if ch == "零":
            total = total * 10
        else:
            total = total * 10 + CN_NUM[ch]
    return total

def extract_volume_title(text):
    """提取卷名: 第一个 # 标题。"""
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else None

def extract_chapter_title(text):
    """提取章名: 第一个 ## 第X章 标题。"""
    m = re.search(r"^##\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else None

def clean_body(body):
    """清理正文: 去 markdown 标题符号(保留标题文字),章末标记对齐。"""
    lines = []
    for line in body.splitlines():
        s = line.strip()
        if re.match(r"^###\s", s):
            lines.append(re.sub(r"^###\s*", "", s))
            continue
        if re.match(r"^##\s", s):
            lines.append(re.sub(r"^##\s*", "", s))
            lines.append("")
            continue
        if re.match(r"^#\s", s):
            continue  # 卷标题跳过
        if s.startswith("**") or s.startswith("*"):
            s = s.replace("**", "").replace("*", "")
        lines.append(s)
    return "\n".join(lines).strip()

def parse_ch_no_from_name(name):
    """从发布 txt 文件名提取章节号。"""
    m = TITLE_RE.match(name.replace(SUFFIX, "").replace(".txt", ""))
    if m:
        return cn_to_int(m.group(1))
    return None

def strip_suffix(name):
    """`第二十一章 我不怕(待整轮回检).txt` → `第二十一章 我不怕.txt`"""
    return name[: -len(f"{SUFFIX}.txt")] + ".txt" if name.endswith(f"{SUFFIX}.txt") else name

def published_chs(vol_dir):
    """返回 {ch_no: 文件名} —— 正式(无后缀)txt。"""
    out = {}
    if vol_dir.is_dir():
        for f in vol_dir.glob("*.txt"):
            no = parse_ch_no_from_name(f.name)
            if no is not None and not f.name.endswith(f"{SUFFIX}.txt"):
                out[no] = f.name
    return out

def pending_batch(vol_dir):
    """返回带待整轮回检后缀的文件列表。"""
    if not vol_dir.is_dir():
        return []
    return sorted(vol_dir.glob(f"*{SUFFIX}.txt"))

def run_check(vol_dir):
    """对卷目录跑标点校验(强制)。"""
    print("\n=== 发布txt标点规范校验 ===")
    r = subprocess.run(["/usr/bin/python3", CHECK_PUNCT, str(vol_dir), "--all"],
                       capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(f"⚠ 发布txt标点规范未通过({r.returncode}处),请修正后重导!")
        sys.exit(1)
    print(" 发布txt标点规范全部通过")

def main():
    if len(sys.argv) < 2:
        print("用法: export_publish.py <项目目录> [--out 发布目录名] [--batch 批次大小]")
        sys.exit(1)
    proj = Path(sys.argv[1])
    manuscripts = proj / "manuscripts"
    if not manuscripts.exists():
        print(f"未找到正文目录: {manuscripts}")
        sys.exit(1)

    out_name = "发布"
    if "--out" in sys.argv:
        idx = sys.argv.index("--out")
        out_name = sys.argv[idx+1] if idx+1 < len(sys.argv) else "发布"
    batch = 10
    if "--batch" in sys.argv:
        idx = sys.argv.index("--batch")
        try:
            batch = max(1, int(sys.argv[idx+1]))
        except (IndexError, ValueError):
            batch = 10

    out_dir = proj / out_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # 读全部 manuscript 章(每文件=一章)
    ms = []
    for f in sorted(manuscripts.glob("ch*.md")):
        m = CH_FILE_RE.match(f.name)
        if not m:
            continue
        text = f.read_text(encoding="utf-8")
        vol_title = extract_volume_title(text)
        ch_title = extract_chapter_title(text) or f.stem
        ms.append((int(m.group(1)), f, vol_title, ch_title))

    if not ms:
        print("无 ch*.md 章文件。")
        sys.exit(0)

    # 按卷名分组(每章各自的卷名,支持分卷;章节号全书连续,卷内也递增)
    vols = {}
    for no, f, vol_title, ch_title in ms:
        vols.setdefault(vol_title or "未命名卷", []).append((no, f, ch_title))

    for vol_name, chapters in vols.items():
        vol_dir_name = re.sub(r'[\\/:*?"<>|]', "_", vol_name).strip()
        vol_dir = out_dir / vol_dir_name
        vol_dir.mkdir(parents=True, exist_ok=True)

        pub = published_chs(vol_dir)
        max_pub = max(pub) if pub else 0
        pend = pending_batch(vol_dir)
        pend_nos = set(parse_ch_no_from_name(p.name) for p in pend)
        pend_nos.discard(None)

        # 新章 = 章节号 > 本卷已正式发布最大号,且不在待检批次
        new_files = [(no, f, ch_title) for no, f, ch_title in chapters
                     if no > max_pub and no not in pend_nos]

        # 1) 新章一律先导出为待整轮回检
        n_export = 0
        for no, f, ch_title in new_files:
            body = re.sub(r"^##\s+.+$", "", f.read_text(encoding="utf-8"), flags=re.M)
            body = re.sub(r"^#\s+.+$", "", body, flags=re.M)
            clean = clean_body(body)
            fname = f"{ch_title}{SUFFIX}.txt"
            if (vol_dir / fname).exists():
                print(f"  =  {ch_title} 已是待检,跳过")
                continue
            (vol_dir / fname).write_text(f"{ch_title}\n\n{clean}\n", encoding="utf-8")
            print(f"   {ch_title} 新导出(待整轮回检)")
            n_export += 1

        # 2) 重新计算当前批次,满轮且全部通过 → 转正式
        pend = pending_batch(vol_dir)
        pend_nos = sorted(parse_ch_no_from_name(p.name) for p in pend)
        promoted = False
        if pend_nos:
            batch_size = max(pend_nos) - min(pend_nos) + 1
            if batch_size >= batch:
                print(f"\n[{vol_name}] 当前批次 {pend_nos} 已满 {batch} 章,整批剥离后缀 → 正式发布:")
                run_check(vol_dir)
                for p in pend:
                    new_name = strip_suffix(p.name)
                    p.rename(vol_dir / new_name)
                    print(f"   {p.name} → {new_name}")
                promoted = True
                pub = published_chs(vol_dir)
                max_pub = max(pub) if pub else 0
            else:
                print(f"\n[{vol_name}] 当前批次 {pend_nos} 共 {batch_size} 章,未满 {batch} 章,保持 (待整轮回检) 状态。")
        elif n_export == 0:
            print(f"[{vol_name}] 无新章导出,发布目录已是最新。")

        if n_export or promoted:
            run_check(vol_dir)

        pub_now = published_chs(vol_dir)
        print(f"\n[{vol_name}] 已正式发布: {len(pub_now)} 章 (最大 {max(pub_now) if pub_now else 0})")
        pend_now = pending_batch(vol_dir)
        if pend_now:
            print(f"[{vol_name}] 待整轮回检: {[parse_ch_no_from_name(p.name) for p in pend_now]} (未满 {batch} 章,回检后自动转为正式)")

if __name__ == "__main__":
    main()
