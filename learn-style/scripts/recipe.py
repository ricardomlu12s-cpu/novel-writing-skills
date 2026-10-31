#!/usr/bin/env python3
"""配方注入引擎 — 把 merge-recipe 的"配方"接上全局资产库,按维度分层注入。

解决问题: 融合多本书时,若把 A+B+C 全混在一起 → 缝合怪。
本脚本读项目的配方文件,按"底盘/调味/人物/情节/情感/世界观"分层,
从全局资产库按维度取对应资产,生成"分层注入清单"(写什么场景取什么资产)。

用法:
  python3 recipe.py inject <项目目录>            # 按配方生成分层注入清单
  python3 recipe.py check <项目目录>             # 检查配方是否防缝合(底盘唯一/成分分层/规避到位)

配方文件: <项目>/recipe.md(见 merge-recipe.md 模板)
资产引用: <项目>/asset-refs.json(见 reuse-assets)
"""
import argparse
import json
import re
import sys
from pathlib import Path


def load_recipe(project):
    p = project / "recipe.md"
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def parse_recipe(text):
    """解析配方,返回 {层级: [成分]}。"""
    layers = {}
    cur = None
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^##?\s*(底盘|调味|人物|情节|情感|世界观|规避|边界)", line)
        if m:
            cur = m.group(1)
            layers.setdefault(cur, [])
            continue
        if cur and line.startswith("-"):
            layers[cur].append(line.lstrip("- ").strip())
    return layers


def load_asset_refs(project):
    p = project / "asset-refs.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []


def inject(project):
    recipe_text = load_recipe(project)
    if not recipe_text:
        print(f"无配方文件: {project / 'recipe.md'}")
        print("配方模板见 merge-recipe.md。至少要有 底盘(主风格) + 规避。")
        sys.exit(1)
    layers = parse_recipe(recipe_text)
    refs = load_asset_refs(project)

    print(f"配方注入 @ {project.name}\n" + "=" * 60)
    if not layers:
        print(" 配方解析为空,检查 recipe.md 格式。")
        return

    # 按层级输出注入清单
    for layer, comps in layers.items():
        print(f"\n【{layer}】")
        for c in comps:
            # 匹配 asset-refs 里的对应资产
            matched = [r for r in refs if r.get("dimension") in _layer_to_dim(layer)]
            if matched:
                src = " / ".join(r.get("source_book", "?") for r in matched)
                print(f"  {c}  ← 注入资产: {src}")
            else:
                print(f"  {c}  ← (未在 asset-refs.json 登记,需先登记资产)")

    # 防缝合检查
    print("\n" + "=" * 60)
    issues = check_anti_sewing(layers)
    if issues:
        print("防缝合检查:")
        for i in issues:
            print(f"   {i}")
    else:
        print(" 防缝合通过: 底盘唯一、成分分层、规避到位")


def _layer_to_dim(layer):
    m = {
        "底盘": ["风格"],
        "调味": ["风格", "手法"],
        "人物": ["角色"],
        "情节": ["情节"],
        "情感": ["风格", "情节"],
        "世界观": ["世界观"],
    }
    return m.get(layer, [])


def check_anti_sewing(layers):
    issues = []
    # 1. 底盘唯一(有且仅有一个主风格)
    chassis = layers.get("底盘", [])
    if len(chassis) > 1:
        issues.append(f"底盘有 {len(chassis)} 个主风格,会缝合 → 只留一个底盘,其他降为调味")
    if len(chassis) == 0:
        issues.append("无底盘 → 全书没有主基调,必缝合")
    # 2. 规避区存在
    if "规避" not in layers and not any("规避" in l for l in layers):
        issues.append("无规避区 → 容易硬搬设定名/台词(防缝合的核心是规避)")
    # 3. 成分分层(同一维度不出现多个来源)
    for layer, comps in layers.items():
        if len(comps) > 2:
            issues.append(f"{layer} 层有 {len(comps)} 个成分,可能越界 → 每层 ≤2 个")
    return issues


def check(project):
    recipe_text = load_recipe(project)
    if not recipe_text:
        print("无配方文件。")
        sys.exit(1)
    layers = parse_recipe(recipe_text)
    issues = check_anti_sewing(layers)
    print(f"配方检查 @ {project.name}")
    for layer, comps in layers.items():
        print(f"  [{layer}] {len(comps)} 成分")
    print("=" * 60)
    if issues:
        for i in issues:
            print(f"   {i}")
    else:
        print("   防缝合通过")


def main():
    p = argparse.ArgumentParser(description="配方注入引擎")
    p.add_argument("cmd", choices=["inject", "check"])
    p.add_argument("project")
    args = p.parse_args()
    project = Path(args.project).expanduser()
    if args.cmd == "inject":
        inject(project)
    else:
        check(project)


if __name__ == "__main__":
    main()
