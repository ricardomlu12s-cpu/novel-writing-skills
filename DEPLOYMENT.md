# Deployment & Compatibility / 部署与兼容性

English | [中文](#中文)

## Install

```bash
git clone https://github.com/ricardomlu12s-cpu/novel-writing-skills.git
cd novel-writing-skills
python3 install.py          # installs to ~/.claude/skills
```

Custom location: `python3 install.py --dir /path/to/skills`

## Update

```bash
python3 update.py   # git pull + reinstall --force
```

## Uninstall

Delete the skill folder under `~/.claude/skills/`. Your writing data (manuscripts, ledgers) stays untouched — it lives in your own project directory.

## Compatibility

### OS
macOS / Linux / Windows, any with Python 3.8+.

### Python
- 3.8+ (scripts use the walrus operator `:=`).
- Standard library only, zero third-party deps.

### Claude Code / other clients
A skill is just "folder + SKILL.md + scripts" — not tied to one client:

| usage | how |
|---|---|
| **Claude Code (CLI)** | `/skill-name` or trigger words |
| **Other clients with a skills dir** (Cursor etc.) | drop the skill folders into their skills dir, or `install.py --dir` |
| **Plain scripts (no AI)** | run them standalone: `python3 write-chapter/scripts/continuity_check.py <project>` |
| **Terminal / direct API** | read SKILL.md as prompt template, call scripts as tools — the logic is plain markdown + python |

### Optional dependency
- `networkx` (optional): only for `ideate` graph mode. Degrades gracefully without it.

## Where project data lives

Skills don't contain your writing data. One novel = one project directory you create:

```
your-novel/
├── manuscripts/  text
├── canon-ledger/ canon
├── characters/   character cards
└── ...
```

Global assets (deconstructions, style libraries) default to `~/.omc/assets/`, overridable:

```bash
export ASSET_ROOT=/your/global/asset/dir
```

## FAQ

**Q: Installed but trigger words don't fire?**
A: Confirm the path is exactly `~/.claude/skills/<name>/SKILL.md` (no extra nesting). Restart Claude Code.

**Q: Python version error?**
A: Need 3.8+. Check `python3 --version`.

**Q: Only want a few skills?**
A: Copy just those folders, or delete unwanted ones after `install.py`.

---

## 中文

### 安装
```bash
git clone https://github.com/ricardomlu12s-cpu/novel-writing-skills.git
cd novel-writing-skills
python3 install.py          # 装到 ~/.claude/skills
```

### 更新 / 卸载
```bash
python3 update.py           # 更新(先 git pull 再重装)
# 卸载: 删 ~/.claude/skills/ 里对应 skill 目录即可,不动你的创作数据
```

### 兼容性
- 系统: macOS / Linux / Windows,有 Python 3.8+ 即可。
- 脚本纯标准库,零第三方依赖。
- skill 本质是"目录 + SKILL.md + 脚本",不依赖特定客户端: Claude Code、Cursor 等支持 skills 目录的工具都行;脚本也可脱离 AI 单独跑。

### 运行时说明(重要)
- **SKILL.md + references/ 是 markdown 指令,Claude 读它们就能工作,不依赖 Python。**
- `scripts/` 是"确定性增强"(硬扫描),需要 Python 3.8+。Windows 用户没 Python 也能用 skill 主体功能,只是少了脚本加分。
- 可选依赖: `networkx`(ideate 图模式),不装会降级为内置概念库。

### 全局资产
拆书产物、风格库默认放 `~/.omc/assets/`,可用 `export ASSET_ROOT=/你的目录` 改位置。
