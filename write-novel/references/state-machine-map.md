# 状态机总览(State Machine Map)

创作链所有状态机的**一页总览**。状态机是创作链的骨架——每个"追踪"都是状态机在跑。

## 全链状态机

| 状态机 | 位置 | 状态流转 | 触发 |
|--------|------|---------|------|
| **伏笔** | build-world `foreshadowing.jsonl` | 开启 → 悬置 → 回收/遗忘 | 每章检测未回收 |
| **承诺** | write-chapter `promises.jsonl` | 立誓 → 未兑现 → 兑现 | 逾期告警 |
| **关系** | build-world `relationships.jsonl` | 敌对 → 结盟 → 对立 | 关系突变须有动机 |
| **战力** | build-world 角色卡 | L1 → L2 → L3(等级推进) | 跳级告警 |
| **成长** | build-world 角色卡 | 渐变 / 顿悟 | 防跳级 |
| **意见分级** | apply-feedback | A 章内 → B 章级 → C 受控 | 读者反馈 |
| **学习节律** | evolve-style `cadence.jsonl` | 未触发 → 小学习 → 中学习 → 大学习 | 结构锚点/信号/间隔 |
| **指纹演进** | evolve-style `evolution/fingerprint-actual.md` | 锁死区 → 健康区 → 失控区 | 双轨对比(防固化) |
| **质量门** | write-chapter | 草稿 → 去AI味 → 门禁 → 定稿 | 每章强制 |
| **飞轮学习** | write-chapter `lessons.md` | 记录 → 沉淀 → 注入下章 | 每章后 |

## 各状态机详情链接
- 伏笔三级递现 → `plan-plot/references/foreshadowing-three-tier.md`
- 战力状态机 → `build-world/references/power-system.md`
- 意见分级 → `apply-feedback/references/triage-matrix.md`
- 学习节律 → `evolve-style/references/cadence-engine.md`
- 指纹演进 → `evolve-style/references/dual-track-fingerprint.md` + `anti-rigidity.md`
- 质量门 → `write-chapter/SKILL.md`
- 飞轮学习 → `write-chapter/references/lessons-flywheel.md`

## 维护规则
- **状态机数据只追加/流转,不删除**(防漂移可追溯)。
- **一个状态机对应一个文件**,不散落。
- 新增追踪需求 → 先查这里有没有对应状态机,复用而非重造。
