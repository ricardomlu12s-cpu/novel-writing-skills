# 多轮执行协议(Multi-Pass Protocol)

拆书是**多轮、一次性成本、产物永久**的流程。本文件定义 Pass 0-3 的执行细则、断点续跑、深度配置。

## 协议总览

```
Pass 0 脚本定位   chapter_split.py 分章 + 每章字数/信号统计(免费,确定性)
Pass 1 分块提取   每 10-20 章一块,LLM 按结构化 schema 提取 → 块级 ledger(JSONL)
Pass 2 合并成典   块级 ledger → 去重合并 → 源作设定库(伏笔跨块配对 opened/payoff)
Pass 3 校验报告   矛盾扫描 + 未填坑清单 + OOC红线 + 吸收/规避 → deconstruct-report
```

## Pass 0 — 脚本定位(免费)

运行 `scripts/chapter_split.py <作品文件.txt> [--max_chars 20000]`:
- **分章**:按章节标题模式切分(第X章/Chapter N/卷等),输出每章起止偏移、字数。
- **信号统计**:每章高频词、句长、特殊段落定位(对齐 absorption-sampling 的轻量扫描风格)。
- **分块建议**:根据总章数输出"每 10-20 章一块"的推荐切块点。
- 输出到 stdout + 可选写 `<项目>/source-canon/_blocks.txt`。

**脚本只定位/统计,不调用 LLM。** 深度提取由 LLM 在 Pass 1 做。

## Pass 1 — 分块提取(LLM,核心)

对每一块(10-20 章)文本,LLM 按**结构化 schema** 提取该块的七层线索,产出**块级 ledger**(JSONL)。

块级 ledger 暂存于 `<项目>/source-canon/_pass1/block{N}.jsonl`,每块一个文件,含该块内:
- 伏笔线索(`foreshadowing` 候选,含 opened 线索)
- 秘密线索(`secrets` 候选)
- 原子事实(`facts`)
- 角色出场/行为线索(`characters` 候选,注意行为边界/红线索)
- 时间事件(`timeline` 候选)
- 因果对(`causality` 候选)
- 细节(`details` 候选)

**关键**:Pass 1 **不判断终态**(某伏笔是已回收还是未填),只记录"我在这块看到的线索"。跨块配对在 Pass 2。

**断点续跑**:每个 block 的 ledger 落盘后即视为完成,中断可跳过已完成块续跑。

**深度配置**:
- `浅拆`(单遍线索):每块只做 1 遍提取,抽取高置信线索。
- `深拆`(多轮全量,默认):每块 2-3 轮(第一轮全面提取 → 第二轮补漏 → 第三轮校验),提取更全。

## Pass 2 — 合并成典(LLM)

读取所有块级 ledger,去重合并 → 生成源作设定库:
- **伏笔跨块配对**:同一伏笔在 block 3 埋、block 9 回收 → 合并成一条 `foreshadowing` 记录,`opened_ch`/`payoff_ch` 配对,状态标 `已回收`;只有埋没回收的 → `未填`。
- **秘密合并**:seen_by 累积、revealed_ch 取最早揭示章。
- **角色卡合并**:多块行为线索聚合成分类标记/硬红线/可演化区/反压缩区。
- **事实去重**:同事实多块出现取最早章 + 累计 known_by。
- **因果链串联**:跨块因果对连成链,标注迟到原因。

写入 `source-canon/` 各产物(格式见 `source-canon-schema.md`)。

## Pass 3 — 校验报告(LLM + 脚本)

对合并后的设定库做**矛盾扫描 + 报告生成**:
1. **矛盾扫描**(确定性优先):
   - 死人复活:grep `facts.jsonl` 死亡后是否又出现活跃事实。
   - 时间冲突:timeline.md 同角色同时出现两个地点。
   - 秘密泄露:secrets 的 revealed_ch 之前,角色是否已用过该信息。
2. **未填坑清单**:所有 `status: 未填` 的伏笔 → 同人可续的资源。
3. **OOC 红线汇总**:各角色卡硬红线汇成清单(供 Phase 3 守卫)。
4. **因果重排候选**:从 causality.md 找"叙述序≠因果序"的事件,标重排候选。
5. **吸收与规避**:可内化的手法/细节 vs 不能硬搬的(标志性台词)。

产出 `source-canon/deconstruct-report.md`。

## 成本与断点模型

- **一次性成本**:几万~几十万 token(取决于作品体量 × 深度配置),产物永久复用。
- **断点续跑**:`_pass1/` 已完成的 block 跳过,不重复消耗。
- **增量更新**:原作续更/换版本 → 只对新增章节跑 Pass 1,再合并。

## 深度配置速查

| 配置 | Pass 1 轮数 | 适用 |
|---|---|---|
| 浅拆 | 1 遍 | 长篇快速摸底 / 低预算 |
| 深拆(默认) | 2-3 遍 | 重点作品,追求伏笔/隐藏信息全量 |

## 与现链脚本风格对齐

- 脚本用 stdlib Python,零依赖(同 absorption-sampling / render_panel 风格)。
- 脚本只做**定位/统计/分块/合并的去重辅助**,深度判断(终态/配对/红线)交给 LLM。
- 产物 schema 与现链 foreshadowing.jsonl / facts.jsonl / clue-ledger 完全兼容(见 source-canon-schema.md)。
