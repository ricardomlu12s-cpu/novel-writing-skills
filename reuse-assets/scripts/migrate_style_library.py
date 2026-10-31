#!/usr/bin/env python3
"""迁移现有风格库到全局资产库。

把 ~/.omc/style-library/*(旧位置)迁移到
~/.omc/assets/style/,并给每个 fingerprint.md 补上标准 asset 标签。

用法:
  python3 migrate_style_library.py [--dry-run]
"""
import argparse
import os
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description="迁移 style-library 到全局资产库")
    p.add_argument("--dry-run", action="store_true", help="只打印不执行")
    args = p.parse_args()

    old_root = Path.home() / ".omc" / "style-library"
    new_root = Path.home() / ".omc" / "assets" / "style"

    if not old_root.exists():
        print(f"源风格库不存在: {old_root}")
        sys.exit(0)

    migrated = 0
    for sub in old_root.iterdir():
        if not sub.is_dir():
            continue
        fp = sub / "fingerprint.md"
        if not fp.exists():
            continue

        new_dir = new_root / sub.name
        if args.dry_run:
            print(f"[dry-run] {sub.name} → {new_dir}")
            continue

        new_dir.mkdir(parents=True, exist_ok=True)
        # 复制 fingerprint.md 和 report.md
        for fn in ("fingerprint.md", "report.md"):
            src = sub / fn
            if src.exists():
                (new_dir / fn).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

        # 补标准标签(frontmatter 里没 source_book/dimension/granularity 时补)
        fp_new = new_dir / "fingerprint.md"
        txt = fp_new.read_text(encoding="utf-8")
        if "source_book:" not in txt:
            header = (
                "---\n"
                f"source_book: {sub.name}\n"
                "dimension: 风格\n"
                "granularity: 骨架\n"
                "tags: []\n"
                "---\n\n"
            )
            fp_new.write_text(header + txt, encoding="utf-8")
        migrated += 1
        print(f" {sub.name} → {new_dir}")

    print(f"\n迁移 {migrated} 个风格库 → {new_root}")
    if not args.dry_run and migrated:
        print("原 style-library 保留(未删除),确认无误后可手动删: rm -rf ~/.omc/style-library")


if __name__ == "__main__":
    main()
