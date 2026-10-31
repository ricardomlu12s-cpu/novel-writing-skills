---
name: reuse-assets
license: MIT
description: 全局创作资产库 — 拆一次书、多本复用、永不串味。把"拆书产物/风格指纹/写作手法/情节模式/世界知识"五类资产从"项目私有"提升为"全局共享",每件资产带来源标签(拆自哪本书)和维度标签(风格/手法/情节/世界观/角色),创作时按配方"引用而非复制"。解决两大痛点:①两本书都要用同一部作品,不必重复拆书烧 token;②多本书资产混放导致串味。触发词:"资产库"/"复用拆书"/"跨书用"/"全局库"/"这本书拆过吗"/"防串味"/"多本书".
allowed-tools: [Bash, Read, Grep, Write, Edit]
---

# 全局创作资产库(Asset Library)

**核心理念**: 拆书、学风格、积累手法,这些"高成本、可复用"的产出,应该**拆一次、全局共享**,而不是绑死在某一本书的项目目录里。本库是创作链的**全局资产层**。

## 为什么需要这一层(两个痛点)

1. **重复拆书烧 token**: 两本书都要用《诡秘之主》的世界观,现在得各拆一次。→ 拆一次进库,多书引用。
2. **多书资产串味**: 角色声线、世界观、手法混在一个项目里,写 B 书时 A 书的味道渗进来。→ 每件资产带**来源标签**,按标签隔离。

## 资产库目录(全局,与项目无关)

```
~/.omc/assets/                        # 全局资产根(可配置)
├── deconstruction/                   # ① 拆书产物(最贵,必须复用)
│   └── <作品名>/source-canon/        #   study-book 的完整产物
│       └── asset.json                #   来源标签 + 维度清单(见下)
├── style/                            # ② 风格指纹(已全局,迁入)
│   └── <风格名>/fingerprint.md
├── technique/                        # ③ 写作手法(白金手法/反套路/金句)
│   └── <手法名>.md
├── plot/                             # ④ 情节模式(钩子/反转/结构骨架)
│   └── <模式名>.md
└── knowledge/                        # ⑤ 世界知识(写过的世界规则/史料/题材)
    └── <领域>.md
```

> 迁移: 你现有的 `~/.omc/style-library/` 就是 style 库的雏形,迁移即可(见 §迁移)。

## 资产标签(防串味的关键)

每件资产顶部必须带 YAML 标签,检索/注入时据此隔离:

```yaml
---
source_book: 诡秘之主        # 拆自哪部作品(原创资产填 "自研")
dimension: 世界观            # 风格 / 手法 / 情节 / 世界观 / 角色
granularity: 骨架           # 骨架(可跨域重组) / 细节(需谨慎,易串味)
tags: [诡异, 序列, 低魔]     # 自由检索标签
---
```

- **`source_book`**: 资产来自哪。**注入 B 书时,默认只引用 B 书配方里点名的 source_book**,不越界。
- **`dimension`**: 五维之一。写对话时只取 `dimension:风格/手法` 里关于"声线"的,不取世界观。
- **`granularity`**: `骨架`(去细节的结构,可安全跨书复用)vs `细节`(具体台词/设定名,只能用于同源书,否则串味)。**这是防串味的核心分界**。

## 引用而非复制(核心机制)

项目**不拷贝**资产内容,只存引用指针:

```json
// 项目根 asset-refs.json
{"dimension":"世界观","source_book":"诡秘之主","asset":"deconstruction/诡秘之主/source-canon","use_as":"世界框架底盘"}
```

- 写章时按引用指针去全局库取,不复制进项目。
- 改一处全局资产,所有引用它的项目同步(避免"各拷贝一份、越改越漂移")。
- 项目私有内容(角色卡/正典/伏笔/关系)**仍留项目内**——只有"可复用"的才进全局库。

## 复用流程

1. **开书时查库**: 说"这本书拆过吗" / 开书时先跑 `scripts/asset_lookup.py <作品名>`,看是否已有拆书产物。
2. **有 → 直接引用**: 在项目 `asset-refs.json` 记引用,跳过重复拆书。
3. **无 → 拆书进库**: study-book 拆完,产物放全局库 `deconstruction/<作品名>/`,带 asset.json 标签。
4. **写章按配方注入**: 由 write-novel 配方层决定"这本书用哪几件资产做哪层",按引用取、按 dimension 分层注入。

## 防串味三闸(强制)

| 闸 | 规则 |
|---|---|
| **来源隔离** | 注入时只取配方点名的 `source_book`;未点名的资产不进本项目上下文 |
| **粒度分界** | `granularity:骨架` 可跨书;`granularity:细节` 仅限同源书(防台词/设定名串味) |
| **维度分层** | 按 `dimension` 分层注入(世界观只进世界设定,手法只进写作指导),不混合 |

**系列模式(作者有意同风格除外)**: 若作者要写"系列作品、共享同一世界观/角色/风格",在配方里显式开 `series_mode: true`,此时允许跨书共享 source_book 的**细节**——这是刻意串味,不是事故。

## 迁移(从现有 style-library)

```bash
# 现有风格库迁入全局资产库
python3 ~/.claude/skills/reuse-assets/scripts/migrate_style_library.py
# 把 ~/.omc/style-library/* 移到 ~/.omc/assets/style/,并补 asset 标签
```

## 检索/查重

```bash
# 查某作品是否已拆过
python3 ~/.claude/skills/reuse-assets/scripts/asset_lookup.py <作品名>
# 按维度+标签检索资产
python3 ~/.claude/skills/reuse-assets/scripts/asset_lookup.py --dimension 世界观 --tag 低魔
```

## 喂给谁 / handoff
- **study-book**: 拆书产物 → 全局库 deconstruction/(而非绑死在项目)。
- **learn-style**: 风格指纹 → 全局库 style/(迁移)。
- **write-novel**: 配方层读 asset-refs.json,按配方引用注入。
- **ideate**: 从 plot/technique 库取"骨架"做跨域联想(见 ideate)。
- **write-chapter**: 写章前查 asset-refs.json,按维度分层取资产注入。
