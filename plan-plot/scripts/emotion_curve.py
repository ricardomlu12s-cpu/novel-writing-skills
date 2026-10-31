#!/usr/bin/env python3
"""情绪曲线 / 读者共鸣检测 — 每章情绪目标→共鸣强度,产出曲线数据(供面板)。

用法:
  python3 emotion_curve.py <项目目录>

读取 .omc/story/<项目>/manuscripts/ch*.md(或目录下章节文件),
输出每章情绪标签 + 共鸣强度,写入 panel/emotion_curve.json。
"""
import json, sys
from pathlib import Path

# 情绪关键词信号
EMOTIONS = {
    "燃": ["热血", "战意", "怒吼", "燃烧", "不屈", "燃"],
    "爽": ["打脸", "碾压", "扬眉吐气", "翻盘", "反杀", "爽"],
    "虐": ["虐", "心碎", "痛苦", "失去", "牺牲", "血泪", "哭"],
    "悬疑": ["谜团", "疑惑", "真相", "是谁", "秘密", "诡异", "线索"],
    "温情": ["温暖", "守护", "相视一笑", "拥抱", "信任", "家人", "情谊"],
    "恐惧": ["恐惧", "绝望", "冷汗", "毛骨悚然", "追兵", "黑暗"],
}

def classify(ch_text):
    scores = {}
    for emo, signals in EMOTIONS.items():
        cnt = sum(1 for s in signals if s in ch_text)
        if cnt:
            scores[emo] = cnt
    if not scores:
        return "平", 1
    top = max(scores, key=scores.get)
    intensity = min(10, 3 + max(scores.values()))
    return top, intensity

def main():
    if len(sys.argv) < 2:
        print("用法: emotion_curve.py <项目目录>")
        sys.exit(1)
    proj = Path(sys.argv[1])
    mans = proj / "manuscripts"
    if not mans.exists():
        print(f"未找到正文目录: {mans}")
        sys.exit(1)
    curve = []
    for f in sorted(mans.glob("ch*.md")):
        text = f.read_text(encoding="utf-8")
        emo, inten = classify(text)
        curve.append({"ch": f.stem, "emotion": emo, "intensity": inten})
    panel_dir = proj / "panel"
    panel_dir.mkdir(parents=True, exist_ok=True)
    (panel_dir / "emotion_curve.json").write_text(
        json.dumps({"curve": curve}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"情绪曲线已生成: {panel_dir / 'emotion_curve.json'}")
    for c in curve:
        print(f"  {c['ch']}: {c['emotion']} (强度 {c['intensity']})")
    if len(curve) >= 3:
        emos = [c["emotion"] for c in curve]
        if len(set(emos)) <= 2:
            print("\n注意:情绪单一,建议近几章加入变化(爽→虐→温情→悬疑交替)")

if __name__ == "__main__":
    main()
