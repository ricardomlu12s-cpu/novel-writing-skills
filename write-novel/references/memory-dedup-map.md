# 记忆与 references 去重映射(Memory Dedup Map)

**问题**:约 40 条方法论记忆与各 skill 的 references 文档高度重叠(如记忆 `kill-decisive` ↔ `plan-plot/references/kill-decisive-guard.md`)。同一方法论有两个载体,更新时容易只改一处 → 两处漂移。

## 去重原则

**方法论正文唯一收在 references;记忆只留指针。** 判断三类:

| 载体 | 存什么 | 为什么 |
|---|---|---|
| **references**(唯一正文) | 方法论/技术流程/参数表/方案细节 | 更新只改一处 |
| **记忆(指针)** | 一句话:该方法在哪份 references + 触发关键词 | 防止方法论两处漂移 |
| **记忆(非指针)** | 用户偏好、项目事实、工作方式 | references 装不下的,才留记忆 |

## 映射表(方法论 → 唯一载体)

| 记忆条目 | 唯一载体(references) | 备注 |
|---|---|---|
| Style Learn | `learn-style/references/style-fingerprint.md` | 记忆改指针 |
| Story Bible | `build-world/SKILL.md`(目录结构) | 记忆改指针 |
| Long Novel | `write-chapter/references/hierarchical-summary.md` | 记忆改指针 |
| Fanfic Deconstruction | `study-book/references/deconstruction-layers.md` | 记忆改指针 |
| De-AI-Slop | `remove-ai-tone/references/ai-slop-patterns.md` | 记忆改指针 |
| Plot Architect | `plan-plot/references/highpoint-schedule.md` | 记忆改指针 |
| Commercial Craft | `plan-plot/references/golden-three-chapters.md` | 记忆改指针 |
| Golden Line | `plan-plot/references/golden-line-gate.md` | 记忆改指针 |
| Platinum Craft | `plan-plot/references/platinum-craft.md` | 记忆改指针 |
| Intellect Duel | `write-mystery/references/reasoning-chain.md` | 记忆改指针 |
| Romance Engine | `write-romance/references/romance-arc.md` | 记忆改指针 |
| Platform Adapt | `adapt-platform/references/platform-modes.md` | 记忆改指针 |
| Reader Feedback | `apply-feedback/references/triage-matrix.md` | 记忆改指针 |
| Token Budget Guard | `write-chapter/references/token-budget-guard.md` | 记忆改指针 |
| Absorption Sampling | `learn-style/references/absorption-sampling.md` | 记忆改指针 |
| Psychodynamic Narrative | `build-world/references/psychodynamic-char.md` | 记忆改指针 |
| Anti-Sewing Merge | `learn-style/references/anti-sewing-merge.md` | 记忆改指针 |
| Kill-Decisive | `plan-plot/references/kill-decisive-guard.md` | 记忆改指针 |
| Battle-Craft | `plan-plot/references/battle-craft.md` | 记忆改指针 |
| Format Control | `remove-ai-tone/references/format-control.md` | 记忆改指针 |
| Novel Creativity | `plan-plot/references/structure-cliche-check.md` | 记忆改指针 |
| Creative Evolution | `evolve-style/SKILL.md` + `references/cadence-engine.md` | 记忆改指针(2026-08-13 补) |
| Open Write Skeleton | `write-novel/references/quick-skeleton.md` | 记忆改指针(2026-08-13 补) |
| Publish Rhythm | `publish-book/SKILL.md` | 记忆改指针(2026-08-13 补) |

## 保留记忆(非指针,不占 references)

| 记忆条目 | 为什么保留 |
|---|---|
| 会话交接协议 | 流程性铁律,跨 skill,references 在 `write-novel/references/session-handoff.md` |
| 进度权威源 | 磁盘为准的教训,跨 skill,references 在 `write-novel/references/session-handoff.md` |
| 活跃小说项目(active-novel-project) | 项目事实(书名/路径/约束),非方法论 |
| 用户六大领域 | 用户画像,非方法论 |

## 更新规则

- **改方法论**:只改 references,记忆指针不动(指针不存细节)。
- **改项目事实**:改记忆,references 不动。
- **新增方法论**:先建 references,记忆加一行指针;禁止直接写全量进记忆。
