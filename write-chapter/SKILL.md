---
name: write-chapter
license: MIT
description: 长篇写作引擎 — 分层摘要冻结(L0正文→L5全书)+ 正典账本(facts/promises/timeline 只追加不改)+ 连续性校验(查死人复活/伏笔未回收/角色缺席)+ 分章质量门。几百章不崩的核心。触发词:"写第X章"/"续写"/"长篇创作"/"连续写"/"更新大纲"。
allowed-tools: [Bash, Read, Grep, Write, Edit]
---

# Long Novel — 长篇写作引擎

**几百章不崩**的核心引擎。核心理念:**让模型只做它擅长的——在结构化上下文中生成叙事片段,记忆靠文件,不靠模型"记得"**。

## 目录结构
```
<项目目录>/
├── manuscripts/        # 正文(定稿):ch001.md, ch002.md ...
├── drafts/             # AI 生成素材(草稿/脑暴),与正文物理隔离
├── summaries/          # 分层摘要:L1单章 → L5全书
├── canon-ledger/       # 正典账本(只追加不改)
│   ├── facts.jsonl     # 原子事实(含原文引用 + known_by)
│   ├── promises.jsonl  # 承诺/誓言(含截止日期)
│   ├── timeline.md     # 时间线
│   └── rules.md        # 世界规则(对应 build-world world.md 的 L1 公理)
└── plan.md             # 大纲(主线架构,受控修改)
```

## 0. 物理隔离纪律(铁律)
- **正文与 AI 素材严格隔离**:所有 AI 生成的脑暴/扩写草稿放 `drafts/`,严禁直接粘贴进 `manuscripts/` 主稿。
- 每一段发布文字必须经过**人脑语言重构与情感注入**(或 remove-ai-tone 去AI味通过)才进主稿。
- 防止"算法味"直接污染定稿。

## 1. 写一章的流水线(分章质量门,9 步闭环)
每章强制走完,9 步缺一不可:
1. **记忆同步**:读当前活跃实体(角色卡/伏笔/摘要) → 装配本章上下文。
   - **强制装配读者反馈**:读最近一批读者反馈(`lessons.md`/`feedback-log.md`),作为软质量(节奏/共鸣)的最终检验输入——不是可选项(见 apply-feedback)。
2. **一致性检查**:对照正典账本,确认本章不与已写事实矛盾。
3. **RAG 回读**(关键节点):写伏笔回收/转折/兑现时,回读相关原文片段(见 `references/rag-recall.md`),防摘要稀释。
4. **硬约束注入**:生成战斗/关键场景前,注入世界观硬约束(见 `references/hard-constraint-prompt.md`)。
5. **风格校准**:对照 learn-style 风格指纹,确认风格一致。
6. **写正文**:注入活跃实体 + 当前章大纲 → 生成草稿(存 drafts/)。
7. **衔接检查**(定稿前先查,见 `references/continuity-review.md`):该兑现伏笔/该出现角色戏份/蝴蝶下游/跨卷承诺——**先查"该兑现的写了没",再质量门**(缺兑现先补写,不过质量门)。
7.5 **质量门**:草稿经去AI味 + 情节检查通过 → 才移入 manuscripts/ 定稿。
   - **软质量分工**(见 `references/quality-division.md`):硬约束(伏笔/命运/蝴蝶/越卷)可量化查;软质量(节奏/共鸣/文学功底)**不量化**——AI 给"本章在细纲位置+结构建议"参考,你读后裁决,读者反馈最终检验。
   - **定稿强制检查清单**(见 `references/final-check-list.md`):9 步逐项打勾,防跳步。
7.6 **进化节律判定**(evolve-style 横切):定稿后跑 `cadence_calc.py <项目目录>` ——读节律账本,判"该学哪层"(结构锚点/信号/间隔三源取最早)。
   - 触发 → 执行对应学习(L1 即时已在此沉淀;L2/L3/L4/L5 按 `evolution_report.py` 决策,重大节点交作者裁决)。
   - 未触发 → 静默(账本已登记,不打断写作流)。
   - **防固化**:写关键/风格敏感章前跑 `rigidity_scan.py`,偏差≈0(锁死区)→ 注入变化/限用令;偏差过大(失控区)→ 拉回。
8. **飞轮沉淀**:每章定稿后,把质量门结果 + 读者反馈 + 手法得失沉淀进 `lessons.md`(见 `references/lessons-flywheel.md`)。
   - **防污染铁律**:只记有证据的(质量门/读者/检测);错误样本只进 Stop/Avoid,不进 Keep;无证据标低置信不注入。
   - **注入**:写下一章前,注入最近 3 条有证据的 lessons(L1 即时学)。
   - **登记节律账本**:`cadence.jsonl` 追加一次 `type:check/learn`(evolve-style 判定输入,append-only)。
   - **刷指纹**:跑 `fingerprint_scan.py` 更新 `evolution/fingerprint-actual.md`(双轨对比输入)。
9. **预算检查**:每写 N 章(经验值 10-20)查累计用量 + 预计下章注入量,超阈值自动询问是否开新会话(见 `references/token-budget-guard.md`)。
   - 同意 → 落盘断点 checkpoint.md + 更新记忆(仅稳定事实,进度写 checkpoint/交接摘要) → 给"续写《书名》"指引。
   - 继续 → 提醒"写完本章建议结束会话"。

## 2. 分层摘要冻结(关键)
```
L0 正文        ch001.md(原文)
L1 单章摘要     summaries/L1/ch001.md
L2 区块摘要     summaries/L2/block01.md(5章合并)
L3 篇章摘要     summaries/L3/arc01.md(一个剧情弧)
L4 卷摘要       summaries/L4/vol01.md(一卷)
L5 全书摘要     summaries/L5/novel.md(顶层)
```

### 2.5 写章前 token 门禁(强制,防"越写越烧")
每章写前跑 `context_budget.py gate`,注入量超上限 → 强制最小上下文装配:
```bash
python3 ~/.claude/skills/write-chapter/scripts/context_budget.py gate <项目目录> [--max-tok 40000]
```
- 核心: 不管写到第 100 章还是第 500 章,**单章注入量恒定**(靠按需检索,不靠全量摘要)。
- 超限时按提示走最小装配(角色卡→lorebook 按需、摘要→只 L5+L4+L3、lessons→1条、RAG→2段)。
**规则**:每层写定即"冻结",不再改动;写新章时只注入 `L5 + 当前卷L4 + 当前弧L3 + 最近区块L2`(低上下文省 token)。完整方案见 `references/hierarchical-summary.md`。

## 3. 正典账本(只追加不改)
- `facts.jsonl`:每行一个原子事实 `{"fact":"主角在第10章获得玉佩","ch":10,"known_by":["主角"],"ref":"ch010"}`。
- `promises.jsonl`:承诺/誓言/伏笔带截止 `{"promise":"誓要复仇","made_ch":5,"deadline_ch":null}`。
- `timeline.md`:时间线(按章追加)。
- **铁律:只追加,不改、不删已写条目**——防止漂移和自我矛盾。

## 4. 连续性校验(借鉴 Continuity Engine 思路)
每章后跑**确定性脚本**(`scripts/continuity_check.py`),无需 LLM 硬扫:
```bash
python3 ~/.claude/skills/write-chapter/scripts/continuity_check.py <项目目录>
```
覆盖:死人复活候选、缺席角色(超阈值章未出现)、伏笔悬置过久、时间线乱序、关系反复翻转、承诺逾期、POV 越界(角色用了不该知道的信息)。
脚本只**标出**不判错(缺席/悬置可能是作者有意),告警须人工复核,见 `references/continuity-engine.md`。

## 5. 分章质量门
- 逻辑:无矛盾、与正典一致、无POV越界。
- 文风:与 learn-style 风格指纹匹配度。
- 结构:章末有钩子、节奏(快/慢档)符合大纲配额(借鉴 novel-creator-skill 的剧情加速禁止)。
- 去AI味:交 **remove-ai-tone** 审查,通过才进定稿。

## 6. 改纲(受控修改)
- 主线架构不可随意改;中途改纲须显式确认,并**级联更新**受影响章节的摘要与正典账本。

## 喂给谁 / handoff
- **build-world**:读设定库(角色卡/伏笔/POV)→ 装配本章上下文;写后回写角色状态。
- **learn-style**:风格指纹 → 校准每章。
- **remove-ai-tone**:草稿 → 去AI味审查 → 定稿。
- **build-world 面板**:写后刷新创作数据面板(进度/伏笔/意见)。
- **evolve-style**:定稿后跑 cadence 判定(L2-L5 学习)+ 刷实际指纹 + rigidity_scan 防固化(见 step 7.6/8)。
- **publish-book**:每 10 章/每卷末走发布回检(检测→润色→排版→发布→反思);**10 章为初值,随篇幅由 cadence 动态重算**。
- 产物:`<项目目录>/`(正文/摘要/账本)。
