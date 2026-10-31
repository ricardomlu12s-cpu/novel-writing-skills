#!/usr/bin/env python3
"""novel-writing-skills 一键安装脚本(跨平台,多语言)。

把本仓库里的 skills 安装到 Claude Code 的 skills 目录,并检查 Python 依赖。
启动时可选语言(English / 中文),后续提示用所选语言。

用法:
  python3 install.py              # 交互式选择语言后安装全部 16 个 skill
  python3 install.py --lang en    # 英文界面
  python3 install.py --lang zh    # 中文界面
  python3 install.py --dir DIR    # 装到指定 skills 目录(默认 ~/.claude/skills)
  python3 install.py --dry-run    # 只检查,不实际拷贝
  python3 install.py --force      # 覆盖已存在的同名 skill

兼容:
  - macOS / Linux / Windows(Python 3.8+)
  - Claude Code(默认)、Cursor 等支持 skills 目录的工具
"""
import argparse
import shutil
import sys
from pathlib import Path

# 本仓库里的 16 个 skill
SKILLS = [
    "write-novel", "study-book", "build-world", "write-chapter",
    "remove-ai-tone", "plan-plot", "write-romance", "write-mystery",
    "adapt-platform", "apply-feedback", "evolve-style", "publish-book",
    "learn-style", "reuse-assets", "ideate", "pipeline",
]

REPO_ROOT = Path(__file__).resolve().parent

# 双语文案
MSG = {
    "en": {
        "select": "Select language / 选择语言 / 言語 / Язык [en/zh/ja/ru] (default: en): ",
        "target": "Install target: {}",
        "dry_run": "[dry-run] The following skills would be installed:",
        "missing_dir": "  MISSING {} (skipped)",
        "install_done": "\nInstall complete: {} installed, {} skipped.",
        "already": "  = {} already exists, skip (use --force to overwrite)",
        "installed": "  OK {}",
        "next": "\nNext: restart Claude Code, then say a trigger word (e.g. \"写小说\").",
        "update": "Update: rerun with --force. Uninstall: delete the skill folder.",
        "py_old": "Python {} too old, need 3.8+ (scripts use walrus operator :=).",
        "nx_ok": "networkx installed (ideate graph mode available)",
        "nx_no": "networkx not installed (optional): ideate degrades to built-in bank",
        "nx_hint": "   for graph mode: pip install networkx",
        "core_note": "Note: core skills target Chinese-language fiction (remove-ai-tone & punctuation are Chinese-specific).",
    },
    "zh": {
        "select": "选择语言 / Select language / 言語 / Язык [en/zh/ja/ru] (默认: zh): ",
        "target": "安装目标: {}",
        "dry_run": "[dry-run] 以下 skill 会被安装:",
        "missing_dir": "   {} 缺目录,跳过",
        "install_done": "\n安装完成: {} 个,跳过 {} 个。",
        "already": "  = {} 已存在,跳过(--force 覆盖)",
        "installed": "   {}",
        "next": "\n下一步: 重启 Claude Code,说触发词如「写小说」即可。",
        "update": "更新: 重新跑 --force;卸载: 删掉目标目录里对应 skill 目录。",
        "py_old": "Python {} 版本过旧,需要 3.8+(脚本用了海象运算符 :=)。",
        "nx_ok": "networkx 已装(ideate 图联想可用)",
        "nx_no": "未装 networkx(可选): ideate 会降级为内置概念库",
        "nx_hint": "   要图联想可装: pip install networkx",
        "core_note": "说明: 核心 skill 面向中文小说创作(去 AI 味/标点规范是中文专用)。",
    },
    "ja": {
        "select": "言語を選択 / Select language [en/zh/ja] (default: en): ",
        "target": "インストール先: {}",
        "dry_run": "[dry-run] 以下のスキルがインストールされます:",
        "missing_dir": "   {} ディレクトリがありません,スキップ",
        "install_done": "\nインストール完了: {} 個,スキップ {} 個。",
        "already": "  = {} は既に存在,スキップ(--force で上書き)",
        "installed": "   {}",
        "next": "\n次へ: Claude Code を再起動し,トリガーワード(例「写小说」)を入力。",
        "update": "更新: --force で再実行。アンインストール: 対象スキルフォルダを削除。",
        "py_old": "Python {} が古すぎます。3.8+ が必要(海象演算子 := を使用)。",
        "nx_ok": "networkx 導入済み(ideate のグラフ連想が利用可能)",
        "nx_no": "networkx 未導入(任意): ideate は内蔵概念バンクにフォールバック",
        "nx_hint": "   グラフ連想を使う場合: pip install networkx",
        "core_note": "注意: コアスキルは中国語小説の創作向け(脱AI臭・句読点は中国語専用)。",
    },
    "ru": {
        "select": "Выберите язык / Select language [en/zh/ja/ru] (default: en): ",
        "target": "Каталог установки: {}",
        "dry_run": "[dry-run] Будут установлены следующие навыки:",
        "missing_dir": "   {} нет каталога, пропуск",
        "install_done": "\nУстановка завершена: {} установлено, {} пропущено.",
        "already": "  = {} уже существует, пропуск (--force для перезаписи)",
        "installed": "   {}",
        "next": "\nДалее: перезапустите Claude Code и введите триггер (например, «写小说»).",
        "update": "Обновление: повторный запуск с --force. Удаление: удалите папку навыка.",
        "py_old": "Python {} слишком старый, нужен 3.8+ (используется моржовый оператор :=).",
        "nx_ok": "networkx установлен (доступен графовый режим ideate)",
        "nx_no": "networkx не установлен (необязательно): ideate перейдёт на встроенный банк",
        "nx_hint": "   для графового режима: pip install networkx",
        "core_note": "Примечание: основные навыки — для китайскоязычной прозы (де-ИИ и пунктуация — китайские).",
    },
}


def default_skills_dir():
    home = Path.home()
    return home / ".claude" / "skills"


def pick_lang(arg_lang):
    if arg_lang in ("en", "zh", "ja", "ru"):
        return arg_lang
    # 交互式选择
    try:
        ans = input("Select language / 言語 / 语言 / Язык [en/zh/ja/ru] (default: en): ").strip().lower()
        if ans in ("zh", "中文", "中", "chinese"):
            return "zh"
        if ans in ("ja", "日本語", "日", "japanese"):
            return "ja"
        if ans in ("ru", "русский", "俄", "russian"):
            return "ru"
        return "en"
    except (EOFError, KeyboardInterrupt):
        return "en"  # 非交互(管道/CI)默认英文


def check_python(lang, m):
    v = sys.version_info
    if v < (3, 8):
        print(m["py_old"].format(f"{v.major}.{v.minor}"))
        return False
    return True


def check_optional(lang, m):
    try:
        import networkx  # noqa: F401
        print(m["nx_ok"])
    except ImportError:
        print(m["nx_no"])
        print(m["nx_hint"])


def install_one(src, dst, force):
    if dst.exists():
        if not force:
            return False
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return True


def main():
    p = argparse.ArgumentParser(description="Install novel-writing-skills")
    p.add_argument("--lang", choices=["en", "zh", "ja", "ru"], help="UI language")
    p.add_argument("--dir", help="skills dir (default ~/.claude/skills)")
    p.add_argument("--dry-run", action="store_true", help="check only")
    p.add_argument("--force", action="store_true", help="overwrite existing skills")
    args = p.parse_args()

    lang = pick_lang(args.lang)
    m = MSG[lang]

    if not check_python(lang, m):
        sys.exit(1)

    dest_dir = Path(args.dir).expanduser() if args.dir else default_skills_dir()
    print(m["target"].format(dest_dir))
    print(m["core_note"] + "\n")

    if args.dry_run:
        print(m["dry_run"])
        for s in SKILLS:
            src = REPO_ROOT / s
            print(f"  {'OK' if src.is_dir() else 'MISSING'} {s}")
        check_optional(lang, m)
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    installed = 0
    skipped = 0
    for s in SKILLS:
        src = REPO_ROOT / s
        if not src.is_dir():
            print(m["missing_dir"].format(s))
            continue
        if install_one(src, dest_dir / s, args.force):
            print(m["installed"].format(s))
            installed += 1
        else:
            print(m["already"].format(s))
            skipped += 1

    print(m["install_done"].format(installed, skipped))
    check_optional(lang, m)
    print(m["next"])
    print(m["update"])


if __name__ == "__main__":
    main()
