# 确定性连续性检查(Continuity Checks)

借鉴 story-skills 的 Continuity Engine 思路:把设定库当契约,像编译器查类型错误一样查叙事矛盾。**确定性优先,LLM 校验兜底**(省钱:先跑免费的,再跑贵的)。

## 检查清单(每章后逐项过)

| # | 检查 | 确定性检测 | LLM 兜底 |
|---|------|-----------|----------|
| 1 | 死人复活 | grep 角色死亡记录 vs 后续出场 | 判断"假死/复活"是否剧情需要 |
| 2 | 缺席角色 | 时间线里角色超5章未出现 | 判断是否该拉回 |
| 3 | 伏笔悬置过久 | 伏笔注册表 status=悬置 且章数差>15 | 判断该回收还是遗忘 |
| 3.5 | 源作伏笔越界(同人) | 同人正文是否让角色用了"源作未回收伏笔"的信息(检查源作侧 `source-canon/foreshadowing.jsonl` + 桥接) | 判断是否泄露/POV 越界 |
| 4 | 时间线漂移 | 章节标注时间 vs 正典账本 timeline | 判断是否合理(如时间跳跃) |
| 5 | 承诺逾期 | promises.jsonl 有 deadline 且超期未兑现 | 判断是否该兑现 |
| 6 | POV 越界 | pov-boundary.jsonl:角色用了 known_by 不含的信息 | 判断是否泄露 |
| 7 | 设定冲突 | 本章设定 vs world.md/rules.md | 判断是否新设定需登记 |
| 8 | 源作设定冲突(同人) | 本章设定 vs `source-canon/canon.md` + 源作角色卡(OOC 检查) | 判断偏离是否已显式登记"偏离原文" |
| 9 | 世界框架守恒(同人) | 本章引入的体系/设定 vs `source-canon/canon.md` **守恒层级**(S/A/B) | 判断是否穿透 S 级绝对公理 |
| 10 | 蝴蝶效应未重排(同人) | `source-canon/butterfly-ledger.jsonl` 中 `status=已登记未重排` 且章数超阈值 | 判断下游因果是否需补排 |
| 11 | 外来公理未磨合(同人) | `source-canon/external-axioms.jsonl` 中 `status=待磨合` 被写入正文 | 判断是否违反 S 级冲突需改造/拒绝 |

> 检查 9 仅同人项目生效。**最高铁律:蝴蝶效应再大,人物/剧情可改,世界背景框架必须守恒。** 本章若引入新体系/新设定,先问:触及守恒层级哪一级?
> - **S 级绝对公理**(如"人死不能复生")→ 不可穿透,违反即破坏世界背景框架,直接告警。
> - **A 级硬框架**(力量体系/势力/地理/时代)→ 改动须登记 + 沿因果链重排,且不与 S 级矛盾。
> - **B 级弹性** → 可合理演化,但须守世界内在逻辑。

> 检查 8 仅在同人项目(`<项目目录>/source-canon/` 存在)时生效。读 `source-canon/canon.md`(L6 世界观骨架 L1 公理)比对本章设定;读源作角色卡 `characters/*.md` 的 **OOC 硬红线区**比对角色行为。同人偏离源作设定/形象,须先在 `deconstruct-report.md` 显式登记"偏离原文"及原因,否则判为告警。

## 确定性检测命令(零成本,先用)
```bash
# 1 死人复活
/usr/bin/grep -n "死亡" canon-ledger/facts.jsonl | /usr/bin/grep -iE "复活|活过来|安然" 
# 2 缺席角色(粗略:统计每个角色名在时间线出现的章数)
/usr/bin/grep -c "角色名" timeline.md
# 3 伏笔悬置
python3 - <<'PY'
import json
for line in open("canon-ledger/facts.jsonl"):  # 实际从 foreshadowing.jsonl 读
    pass
PY
# 5 承诺逾期
python3 - <<'PY'
import json
for line in open("canon-ledger/promises.jsonl"):
    p = json.loads(line)
    if p.get("deadline_ch") and not p.get("paid_ch"):
        print(f"逾期承诺: {p.get('promise')} (截止第{p.get('deadline_ch')}章)")
PY
# 3.5 源作伏笔越界(同人):源作伏笔只读,不可被同人"提前消费"
if [ -f "source-canon/foreshadowing.jsonl" ]; then
  echo "--- 源作伏笔越界检查(同人) ---"
  python3 - <<'PY'
import json, os
src = "source-canon/foreshadowing.jsonl"
mine = "foreshadowing.jsonl"
if os.path.exists(src):
    for line in open(src, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        f = json.loads(line)
        # 源作侧未回收的伏笔 → 同人侧不可提前用其信息(除非有桥接登记)
        if f.get("status") == "悬置" and f.get("payoff_ch") is None:
            print(f"[源作未回收] {f.get('id')}: {f.get('desc')} — 同人侧若消费此信息须桥接登记")
# 桥接检查:同人侧 type=bridge 的条目标注回收了哪个源作伏笔
if os.path.exists(mine):
    for line in open(mine, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        m = json.loads(line)
        if m.get("type") == "bridge":
            print(f"[桥接] 同人 {m.get('to')} ↔ 源作 {m.get('src')} (章{m.get('ch')})")
PY
fi
# 8 源作设定冲突(同人):存在 source-canon 才检查
if [ -d "source-canon" ]; then
  echo "--- 源作设定冲突检查(同人) ---"
  # OOC 硬红线:源作角色卡中的红线区,与本章正文比对
  /usr/bin/grep -l "绝不做" source-canon/characters/*.md 2>/dev/null | while read f; do
    echo "[OOC红线] $f"
    /usr/bin/grep -A3 "绝不做" "$f"
  done
fi
# 9 世界框架守恒(同人):查 canon.md 守恒层级 S 级公理,与本章引入体系比对
if [ -f "source-canon/canon.md" ]; then
  echo "--- 世界框架守恒检查(同人) ---"
  echo "[守恒层级] canon.md 中标注 S级/A级/B级 的条目:"
  /usr/bin/grep -E "S级|A级|B级|绝对公理|硬框架|弹性" source-canon/canon.md | /usr/bin/head -20
  echo "(本章引入新体系/设定时,核对是否穿透 S 级绝对公理;A级需登记+重排;B级守逻辑)"
fi
# 10 蝴蝶效应未重排(同人):查账本中"已登记未重排"的条目
if [ -f "source-canon/butterfly-ledger.jsonl" ]; then
  echo "--- 蝴蝶效应未重排检查(同人) ---"
  python3 - <<'PY'
import json, os
p = "source-canon/butterfly-ledger.jsonl"
if os.path.exists(p):
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        b = json.loads(line)
        if b.get("status") == "已登记未重排":
            print(f"[待重排] {b.get('id')}: {b.get('change')} (触发章 {b.get('triggered_ch')}, 下游 {b.get('affected_causality')})")
PY
fi
# 11 外来公理未磨合(同人):查 external-axioms 中 status=待磨合 的条目
if [ -f "source-canon/external-axioms.jsonl" ]; then
  echo "--- 外来公理未磨合检查(同人) ---"
  python3 - <<'PY'
import json, os
p = "source-canon/external-axioms.jsonl"
if os.path.exists(p):
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        e = json.loads(line)
        if e.get("status") == "待磨合":
            print(f"[待磨合] {e.get('id')}: {e.get('axiom')} (挂 {e.get('target_level')}, 与S级: {e.get('compat_with_s')})")
PY
fi
```
> 注意:本 shell 中 `grep/find` 可能被 bun 别名注入,连续性检测命令**显式用 `/usr/bin/grep`**。

## 输出
- 检查结果写入 `<项目目录>/panel/`(供创作数据面板显示"创作意见区")。
- 有告警 → 交回作者/创作意见区,通过后才能进下一章。

## 原则
1. **确定性优先**:能 grep/python 查的不动用 LLM。
2. **误报容忍**:确定性检测可能误报(如"假死"),交给 LLM 兜底判断。
3. **只追加**:账本只加不改,确保可追溯。
