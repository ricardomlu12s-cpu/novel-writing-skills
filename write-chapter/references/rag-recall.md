# RAG 按需回读(防摘要稀释 + token 可控)

**核心**:分层摘要+按需回读 = "摘要找位置、原文保细节"。既控制 token(不灌全文),又不丢细节(回读原文)。

## 为什么需要 RAG
只读压缩摘要会导致:
- 人物形象扁平(丢了"怎么走到这步")。
- 情节失动机(丢了"为什么")。
- 伏笔找不到呼应物(细节被压掉)。

RAG 让模型写某场景时,**检索相关原文片段回读**,而不是靠摘要"记得"。

## 回读触发时机
| 场景 | 回读什么 |
|------|---------|
| 伏笔回收 | 该伏笔的开启章原文(`foreshadowing.jsonl` 的 `opened_ch`) |
| 角色过往选择 | 该角色关键转折章原文(角色卡 ref) |
| 承诺兑现 | 承诺成立章原文(`promises.jsonl` 的 `made_ch`) |
| 设定调用 | 相关世界观/战力条目(`power-system.md`) |
| 关系演变 | 关系变更章原文(`relationships.jsonl` 的 `ch`) |

## 实现(轻量 BM25,无需 embedding)
```bash
# 对项目正文建索引(FTS5,零依赖,适配 <项目目录>/manuscripts/ 结构)
python3 ~/.claude/skills/write-chapter/scripts/build_index.py build <项目目录>

# 检索相关片段(Top-K=3~5),注入上下文
python3 ~/.claude/skills/write-chapter/scripts/build_index.py search <项目目录> "玉佩 刻痕" --top 3
```
- FTS5 检索相关章节片段(Top-K=3~5),注入上下文。
- 无 embedding/API 依赖 → 免费、可控、CJK 友好。
- 索引文件 `<项目目录>/.index/retrieval.db`,可随时删掉重建。

## Token 预算
- 每章注入:分层摘要(L5+L4+L3+L2,固定大小)+ 活跃实体卡 + **RAG 回读片段(≤3段,每段~500字)**。
- 总注入量恒定,不随总章数增长(几百章后单章成本≈第10章)。

## 与分层摘要衔接
- 摘要 = 卡片目录(知道书在哪、讲什么)。
- 原文 L0 = 书(引用时翻书,不走目录)。
- 正典账本 = 校验层(事实/承诺/时间线只追加)。

## 防稀释原则
1. **原文永存 L0**,永不删除、永不压缩。
2. **关键实体有独立账本**(facts/promises/timeline/foreshadowing/relationships),不靠摘要"记得"。
3. **回读优先**:写关键节点(伏笔回收/转折/兑现)时,RAG 回读原文,不用摘要代替。
