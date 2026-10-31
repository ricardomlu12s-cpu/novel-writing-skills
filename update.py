#!/usr/bin/env python3
"""novel-writing-skills 更新脚本(跨平台)。

拉取最新版后重跑安装即可。本脚本等价于 install.py --force,
但会额外保留用户自己的 state/项目数据(因为那些本来就不在 skill 目录里)。

用法:
  python3 update.py
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
INSTALL = REPO_ROOT / "install.py"


def main():
    # 如果是从 git 仓库运行,先 pull
    git_dir = REPO_ROOT / ".git"
    if git_dir.exists():
        print("检测到 git 仓库,先拉取最新代码...")
        try:
            subprocess.run(["git", "-C", str(REPO_ROOT), "pull"], check=True)
        except subprocess.CalledProcessError as e:
            print(f" git pull 失败({e}),继续用本地文件重装")
    else:
        print("非 git 仓库,直接用当前目录重装")

    # 强制重装
    cmd = [sys.executable, str(INSTALL), "--force"]
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
