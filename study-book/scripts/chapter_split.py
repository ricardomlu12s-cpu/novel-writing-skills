#!/usr/bin/env python3
"""
chapter_split.py — 拆书引擎 Pass 0:分章 + 每章字数/信号统计(免费,确定性)。

职责(对齐 absorption-sampling 的"脚本只定位/统计,LLM 做深度提取"哲学):
  1. 分章:按章节标题模式切分,输出每章序号/标题/起止偏移/字数。
  2. 信号统计:每章句长、高频词、特殊段落定位(细节/伏笔/隐藏线索信号)。
  3. 分块建议:根据总章数输出"每 10-20 章一块"的推荐切块点(供 Pass 1)。
  4. 输出:stdout + 可选写块清单到 <目标>/_blocks.txt。

零依赖:仅 stdlib(sys/re/pathlib/collections)。
不调用 LLM。深度提取(伏笔配对/终态判断/红线)由 LLM 在 Pass 1-3 做。

用法:
  python3 chapter_split.py <作品.txt> [--out <dir>] [--block 15] [--top 10]
"""

import sys
import re
from pathlib import Path
from collections import Counter

# 章节标题模式(按出现优先级匹配)
CH_PATTERNS = [
    (re.compile(r'^\s*第\s*([0-9一二三四五六七八九十百千零两]+)\s*章\s*(.*)$'), '第X章'),
    (re.compile(r'^\s*第\s*([0-9一二三四五六七八九十百千零两]+)\s*节\s*(.*)$'), '第X节'),
    (re.compile(r'^\s*Chapter\s+([0-9]+)\s*[-:：]?\s*(.*)$', re.IGNORECASE), 'Chapter N'),
    (re.compile(r'^\s*CHAPTER\s+([0-9]+)\s*[-:：]?\s*(.*)$'), 'CHAPTER N'),
    (re.compile(r'^\s*第\s*([0-9一二三四五六七八九十百千零两]+)\s*卷\s*(.*)$'), '第X卷'),
    (re.compile(r'^\s*[【\[(（]?\s*([0-9一二三四五六七八九十百千零两]+)\s*[】\])）]?\s*$'), '数字标题'),
]

# 信号维度关键词(轻量定位,供 Pass 1 定向采样;对齐 absorption 风格)
SIGNAL_KEYWORDS = {
    '伏笔': ['玉佩', '信物', '预言', '警告', '奇怪', '不对劲', '秘密', '线索', '可疑', '伏笔', '遗物', '信', '暗示'],
    '隐藏信息': ['其实', '真相', '原来', '伪装', '身份', '隐瞒', '秘密', '卧底', '内鬼', '身世', '真面目', '隐藏'],
    '因果': ['因为', '所以', '因此', '导致', '结果', '于是', '既然', '既然', '才', '由于', '原因'],
    '时间跳变': ['回忆', '当年', '三年前', '从前', '后来', '多年后', '之前', '那时', '当初'],
    '人物立人': ['他说', '她说', '道', '想', '心', '眼神', '沉默', '淡淡', '冷笑', '皱眉', '动作'],
    '世界观': ['规则', '境界', '力量', '体系', '阵营', '宗门', '帝国', '灵力', '系统', '法则', '位面'],
}

CN_NUM = '零一二三四五六七八九十百千两'


def split_chapters(text):
    """按章节标题模式切分,返回 [(start, title, body)]。"""
    lines = text.split('\n')
    chapters = []
    cur_start = 0
    cur_title = '(开头)'
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        for pat, kind in CH_PATTERNS:
            m = pat.match(stripped)
            if m:
                chapters.append((cur_start, cur_title, '\n'.join(lines[cur_start:i])))
                cur_start = i
                cur_title = stripped[:40]
                break
    chapters.append((cur_start, cur_title, '\n'.join(lines[cur_start:])))
    # 过滤掉空壳(只有标题无正文)
    chapters = [(s, t, b) for s, t, b in chapters if b.strip()]
    return chapters


def sent_len_stats(body):
    """均句长 + 方差(粗粒度,按句末标点切)。"""
    sents = [s for s in re.split(r'[。！？!?…]', body) if s.strip()]
    if not sents:
        return 0.0, 0.0
    lens = [len(s) for s in sents]
    avg = sum(lens) / len(lens)
    var = sum((x - avg) ** 2 for x in lens) / len(lens)
    return round(avg, 1), round(var, 1)


def top_words(body, top_n=10):
    """高频 2-4 字词(粗分词:按标点/空白切块取相邻字符)。"""
    cleaned = re.sub(r'[\s，。！？、；：""''()（）—…·《》<>「」【】　]', ' ', body)
    cand = re.findall(r'[一-鿿]{2,4}', cleaned)
    return Counter(cand).most_common(top_n)


def signal_scan(body):
    """每维关键词命中数。"""
    out = {}
    for dim, kws in SIGNAL_KEYWORDS.items():
        out[dim] = sum(body.count(k) for k in kws)
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    if not src.exists():
        print(f'找不到文件: {src}')
        sys.exit(1)

    out_dir = None
    block_size = 15
    top_n = 10
    args = sys.argv[2:]
    while args:
        a = args.pop(0)
        if a == '--out' and args:
            out_dir = Path(args.pop(0))
        elif a == '--block' and args:
            block_size = int(args.pop(0))
        elif a == '--top' and args:
            top_n = int(args.pop(0))

    text = src.read_text(encoding='utf-8')
    chapters = split_chapters(text)

    print(f'=== 拆书 Pass0:分章与信号统计 ===')
    print(f'来源: {src}')
    print(f'总字数: {len(text)} | 章节数: {len(chapters)}')
    print()

    block_hints = []
    per_chapter = []
    for idx, (start, title, body) in enumerate(chapters, 1):
        avg, var = sent_len_stats(body)
        words = top_words(body, top_n)
        sig = signal_scan(body)
        chars = len(body)
        per_chapter.append((idx, title, chars))
        strong_dims = ', '.join(f'{k}@{v}' for k, v in sig.items() if v > 0)
        print(f'[第{idx:>3}章] {title}')
        print(f'    字数 {chars} | 均句长 {avg} | 句长方差 {var}')
        if strong_dims:
            print(f'    信号: {strong_dims}')
        if words:
            print(f'    高频词: {", ".join(f"{w}×{c}" for w, c in words)}')
        print()

    # 分块建议
    n = len(chapters)
    starts = list(range(1, n + 1, block_size))
    print('=== 分块建议(供 Pass 1) ===')
    print(f'每块 {block_size} 章,共 {len(starts)} 块:')
    for b in starts:
        end = min(b + block_size - 1, n)
        print(f'  Block {b//block_size + 1}: 第{b}-{end}章')
    block_hints = [f'第{b}-{min(b + block_size - 1, n)}章' for b in starts]

    # 可选写块清单
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        block_file = out_dir / '_blocks.txt'
        block_file.write_text('\n'.join(block_hints) + '\n', encoding='utf-8')
        print(f'\n分块清单已写入: {block_file}')

    print(f'\n=== 学习/拆书价值画像(轻量) ===')
    total_sig = Counter()
    for _, _, body in chapters:
        for k, v in signal_scan(body).items():
            total_sig[k] += v
    ranked = total_sig.most_common()
    if ranked:
        strongest = ranked[0][0]
        print(f'全作信号最强维度: {strongest}(线索密集处优先深挖)')


if __name__ == '__main__':
    main()
