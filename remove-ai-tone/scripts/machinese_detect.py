#!/usr/bin/env python3
"""机器化表达量化检测(Machinese Detect)— 按语言学研究数据量化"词汇贫乏/句式单调"。

依据(用户提供 + Pennebaker 等研究):
- 词汇重复率: AI 文本平均高出人类 23%
- 句式变化指数 SVR: 机器仅为人类 68%
- 转场词频率: AI 比人类高 31%("然而/因此"等)
- 模板化段落: 80% AI 段落遵循「论点-解释-例子」固定模式

用法:
  python3 machinese_detect.py <文件.txt>

输出: 四项量化指标 + 对照基准 + 告警(哪些超标)。
"""
import re, sys
from pathlib import Path

# 转场词(AI 过度依赖)
TRANSITIONS = [
    "然而", "因此", "此外", "首先", "其次", "最后", "综上所述",
    "值得注意的是", "与此同时", "不得不说", "总而言之", "也就是说",
    "换句话说", "其实", "真的", "真的", "的确", "确实", "当然",
    "不过", "但是", "然而", "而且", "况且", "何况",
]

# 表层情绪词(浮于表面,缺复杂层次)
SURFACE_EMOTION = ["高兴", "悲伤", "愤怒", "开心", "难过", "生气", "害怕", "幸福", "痛苦", "快乐"]

# 模板化段落信号
TEMPLATE_OPENERS = ["首先", "其次", "最后", "总的来说", "这说明", "由此可见", "不难看出", "显然", "值得注意的是"]
TEMPLATE_CLOSERS = ["因此", "所以", "总而言之", "综上所述", "这告诉我们", "由此可见"]

def ttr(text):
    """类符形符比(Type-Token Ratio): 词汇丰富度(越高越丰富)"""
    tokens = re.findall(r"[一-鿿]{1,4}", text)
    if not tokens:
        return 0
    return len(set(tokens)) / len(tokens)

def svr(text):
    """句式变化指数(SVR): 句长标准差(机器句长均匀 → 低)"""
    sents = [s for s in re.split(r"[。！？…]", text) if len(s) > 1]
    if len(sents) < 3:
        return 0
    lens = [len(s) for s in sents]
    avg = sum(lens) / len(lens)
    var = (sum((l - avg) ** 2 for l in lens) / len(lens)) ** 0.5
    return var

def transition_density(text):
    """转场词密度: 每千字转场词数"""
    n = len(text)
    count = sum(1 for t in TRANSITIONS if t in text)
    return count / (n / 1000) if n else 0

def template_ratio(text):
    """模板化段落比例: 段落以模板开头+结尾的比例"""
    paras = [p for p in text.split("\n") if len(p) > 20]
    if not paras:
        return 0
    templated = sum(1 for p in paras if any(o in p[:10] for o in TEMPLATE_OPENERS) and any(c in p for c in TEMPLATE_CLOSERS))
    return templated / len(paras)

def surface_emotion_density(text):
    """表层情绪词密度: 每千字表层情绪词(高兴/悲伤等)"""
    n = len(text)
    count = sum(1 for e in SURFACE_EMOTION if e in text)
    return count / (n / 1000) if n else 0

def main():
    if len(sys.argv) < 2:
        print("用法: machinese_detect.py <文件.txt>")
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8")

    t = ttr(text)
    s = svr(text)
    td = transition_density(text)
    tr = template_ratio(text)
    sed = surface_emotion_density(text)

    print("=== 机器化表达量化检测 ===")
    print(f"文本字数: {len(text)}")
    print(f"\n1. 词汇丰富度(TTR): {t:.3f}  (人类基线 ~0.50+, <0.40 词汇贫乏)")
    print(f"   {' 词汇贫乏' if t < 0.40 else ' 词汇丰富'}")
    print(f"\n2. 句式变化(SVR): {s:.1f}  (机器仅人类68%; <3 句式单调)")
    print(f"   {' 句式单调' if s < 3 else ' 句法多变'}")
    print(f"\n3. 转场词密度: {td:.1f}/千字  (人类基线 ~8-12, >14 过度依赖)")
    print(f"   {' 转场词过度' if td > 14 else ' 转场自然'}")
    print(f"\n4. 模板化段落: {tr*100:.0f}%  (AI基线 80%, >50% 模板化)")
    print(f"   {' 模板化严重' if tr > 0.5 else ' 结构自然'}")
    print(f"\n5. 表层情绪词: {sed:.1f}/千字  (>3 浮于表面, 缺复杂情感)")
    print(f"   {' 情绪表层化' if sed > 3 else ' 情绪有层次'}")

    flags = sum([t < 0.40, s < 3, td > 14, tr > 0.5, sed > 3])
    print(f"\n{' 命中 ' + str(flags) + ' 项, 建议改写' if flags >= 2 else ' 机器化程度低'}")

if __name__ == "__main__":
    main()
