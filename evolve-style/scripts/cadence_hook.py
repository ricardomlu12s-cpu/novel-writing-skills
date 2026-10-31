#!/usr/bin/env python3
"""cadence_hook.py — 章节定稿 Stop hook 入口(evolve-style)
每次 Claude 结束回合后调用。扫描 ~/.omc/story/*/ 下所有项目,
对"有新增定稿章(manuscripts 数量变化)"的项目跑 cadence_calc --append。
纯本地、纯确定性、无模型/网络调用(适配本地代理 env,不触发网络)。

用法(settings.json hook):
  "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "python3 ~/.claude/skills/evolve-style/scripts/cadence_hook.py --silent"}]}]

退出码: 0 = 正常(无新增或已登记), 1 = 有项目触发学习(供 Stop hook 输出)。
"""
import json
import os
import re
import subprocess
import sys

STORY_ROOT = os.environ.get("STORY_ROOT") or os.path.expanduser("~/.omc/story")
CADENCE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cadence_calc.py")

# 记录上次各项目 manuscripts 数(放 ~/.claude/skills/evolve-style/state/)
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "state", "cadence_hook_state.json")
STATE_FILE = os.path.abspath(STATE_FILE)


def load_state():
    try:
        if os.path.isfile(STATE_FILE):
            with open(STATE_FILE, encoding="utf-8") as fh:
                return json.load(fh)
    except Exception:
        pass
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_FILE)


def count_manuscripts(proj):
    mdir = os.path.join(proj, "manuscripts")
    if not os.path.isdir(mdir):
        return 0
    return sum(1 for f in os.listdir(mdir) if re.match(r"^ch\d{3}\.md$", f))


def latest_chapter(proj):
    mdir = os.path.join(proj, "manuscripts")
    if not os.path.isdir(mdir):
        return None
    nums = [int(m.group(1)) for f in os.listdir(mdir)
            if (m := re.match(r"^ch(\d{3})\.md$", f))]
    return max(nums) if nums else None


def main():
    silent = "--silent" in sys.argv
    if not os.path.isdir(STORY_ROOT):
        if not silent:
            print("no story root")
        return 0

    state = load_state()
    triggered = False
    changed = False

    for name in sorted(os.listdir(STORY_ROOT)):
        proj = os.path.join(STORY_ROOT, name)
        if not os.path.isdir(proj):
            continue
        cur = count_manuscripts(proj)
        prev = state.get(name, 0)
        latest = latest_chapter(proj)

        if cur > prev and latest:
            # 有新增定稿章 → 对该项目跑 cadence 判定 + append 登记
            try:
                res = subprocess.run(
                    [sys.executable, CADENCE_SCRIPT, proj, "--append", "--silent"],
                    capture_output=True, text=True, timeout=60)
                out = (res.stdout or "") + (res.stderr or "")
                # 判定是否触发学习
                if "触发学习" in out:
                    triggered = True
                    if not silent:
                        print(f"[hook] {name}: 第{latest}章触发学习\n{out}")
                else:
                    if not silent:
                        print(f"[hook] {name}: 第{latest}章已登记(cadence)")
            except Exception as exc:
                if not silent:
                    print(f"[hook] {name}: 脚本异常 {exc}")
            state[name] = cur
            changed = True

    if changed:
        save_state(state)

    if not silent and not changed:
        print("[hook] 无新增定稿章,跳过")
    return 1 if triggered else 0


if __name__ == "__main__":
    sys.exit(main())
