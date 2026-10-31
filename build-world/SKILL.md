---
name: build-world
license: MIT
description: 小说设定管理库 — 世界观/角色卡/地点图/伏笔注册表/POV知识边界,并渲染「创作数据面板」(HTML,浏览器查看)展示世界框架/情节走向/角色卡/故事数据,附创作后续意见供修改。支撑几百章不崩的"设定库"。战力数值校验(跳级/越级/成长曲线)也归这里。触发词:"建世界观"/"写角色卡"/"设定框架"/"看创作面板"/"故事数据"/"伏笔状态"/"战力崩了"。
allowed-tools: [Bash, Read, Grep, Write, Edit]
---

# Story Bible — 设定管理库 + 创作数据面板

管理一部长篇的全部"设定骨架",并**渲染成可视面板**供你参考修改。几百章不崩的第一道防线。

## 设定库目录结构
每个项目一个目录:
```
<项目目录>/
├── world.md            # 世界观(规则/势力/地理/历史)
├── characters/         # 人物卡(每人一卡)
│   ├── 001-主角.md
│   └── ...
├── locations.md        # 地点图
├── foreshadowing.jsonl # 伏笔注册表(开启/悬置/回收 状态)
├── pov-boundary.jsonl  # POV 知识边界(谁知道什么秘密)
├── relationships.jsonl # 动态关系网(宿敌结盟/挚友对立的演变)
├── timeline.md         # 时间线
└── panel/              # 渲染出的创作数据面板
    └── index.html
```

## 1. 世界观(world.md)
- 世界规则(L1 公理层,永不漂移)、势力/地理/历史。
- 规则变更必须显式登记(可改,但要记录在案,防矛盾)。

## 2. 角色卡(characters/*.md)
每人一卡,含:
```markdown
# 角色: <名>
## 基础
- 身份/年龄/外貌/性格(三句内)
## 四维卡(商业级角色核心)
- 显性目标: <渴望向外界展示的伪装/短期追求>
- 隐性需求: <灵魂深处真正缺、需故事历程补完的品质>
- 创伤心结: <过去阴影,构成行动内部阻力>
- 言语防线: <独特说话习惯/刻意回避话题>
## 反差感
- 身份 vs 性格 vs 行为: <如 冷酷魔教杀手 × 强迫症 + 动物收集癖>
## 声线
- 口头禅/句式/词汇域/回避: <见 references/voice-lines.md>
## 成长弧线
- <阶段1> → <阶段2> ...
## 状态追踪
- 当前所在章节/健康/关系/目标
## 知识边界(POV)
- 知道:<秘密A、秘密B>
- 不知道:<秘密C>
## 刻画手法参考
- <来自 learn-style 风格指纹:这个角色用哪种手法立人>
## 战力
- 等级: <如 L4 筑基>
- 战力值: <如 120,同级参考 100>
- 成长曲线: <如 卷1 L2→L3, 卷2 L3→L4>
- 越级记录: <无 / 1次(有代价)>
## 成长节奏
- 类型: <渐变 / 顿悟>
- 上次变化: <第X章,从__到__>
- 合理性: <防跳级:单卷跳跃>2级即告警>
```

## 3. 战力系统(防崩坏)
- 完整框架见 `references/power-system.md`。
- 等级框架 + 平衡约束 + 成长曲线,存 `<项目目录>/power-system.md`。
- 战力校验(确定性优先):
  - **跳级**:单卷等级跳跃 > 2 级 → 告警(除非有奇遇+副作用登记)。
  - **越级**:越级挑战成功须有代价(爆种/秘法/牺牲)。
  - **同级平衡**:同级战力差 > 30% → 告警。
  - **成长曲线**:等级与章节进度匹配(约1级/卷)。
- 校验进 write-chapter 质量门(战力崩坏 → 打回)。

## 4. 伏笔注册表(foreshadowing.jsonl)
```json
{"id":"f001","desc":"主角身世的玉佩","opened_ch":12,"status":"悬置","payoff_ch":null}
{"id":"f002","desc":"神秘人警告","opened_ch":20,"status":"回收","payoff_ch":45}
```
状态机:`开启 → 悬置 → 回收/遗忘(触发告警)`。每章检查未回收伏笔,防"挖坑不填"。

### 4.0 伏笔账本分治(同人项目必读)
**同人项目源作伏笔与同人伏笔必须分开**,否则防OOC/防设定冲突检查会误判:
- **源作伏笔** = 拆书产物(`source-canon/foreshadowing.jsonl`),**只读**,是防OOC红线的依据,**永不流转、永不改**。
- **同人伏笔** = 本表(`foreshadowing.jsonl`),**可追加可流转**,是创作空间。
- **桥接**:同人伏笔回收源作伏笔 → 源作 `payoff_ch` 不改,记同人侧 `{"type":"bridge","src":"源作f002","to":"同人f003","ch":58}`;同人重排导致源作伏笔失效 → 记 `butterfly-ledger.jsonl`。
- 面板分两栏显示。完整分治表见 `references/foreshadowing-registry.md`。

## 5. POV 知识边界(pov-boundary.jsonl)
追踪"谁知道什么秘密",防止角色使用未获得的信息(全知视角暴露)。

## 5.5 动态关系网(relationships.jsonl)
追踪角色关系的演变(宿敌结盟/挚友对立的戏剧张力):
```json
{"a":"主角","b":"宿敌","rel":"敌对","ch":12}
{"a":"主角","b":"宿敌","rel":"短暂结盟","ch":58,"note":"对抗更大危机"}
```
- 每章回写关系变化;关系突变须有动机(不突然翻转)。
- 面板显示关系网络状态。
- **当前态 + 演变时间线 + 突变检测**(新):跑 `progression.py`,从只追加账本重建"现在什么关系 + 怎么一步步变的",并标出无动机的突变:
  ```bash
  python3 ~/.claude/skills/build-world/scripts/progression.py <项目目录>
  # 只看某对: --pair 主角 女主
  ```
- **Lorebook 按需注入**(新,省 token):写场景时只注入命中的设定块,不读全量设定库(实测省 96%):
  ```bash
  python3 ~/.claude/skills/build-world/scripts/lorebook.py build  <项目目录>
  python3 ~/.claude/skills/build-world/scripts/lorebook.py inject <项目目录> --query "主角 言灵 战斗" --top 5
  ```
  配合 write-chapter 写章时的"活跃实体装配",把全量角色卡读替换成场景关键词检索,消除"角色卡占单章注入 60%"的隐性大头。

## 5.6 角色声线库
- 每个核心角色独立词汇库+句式偏好,防说话均质化。完整方案见 `references/voice-lines.md`。

## 6. 渲染创作数据面板(核心)
每章后自动渲染 `panel/index.html`,`open` 打开浏览器查看:
```
open <项目目录>/panel/index.html
```
面板全量展示:**世界框架**(势力/规则)、**情节走向**(主线进度/章节地图)、**角色卡**(状态/关系/成长)、**故事数据**(章数/字数/节奏)、**伏笔状态**(开启/悬置/回收表)、**创作后续意见**。

渲染逻辑:读取设定库 JSON/MD → 生成静态 HTML(零依赖,浏览器即可开)。刷新:每章后重新跑渲染器。

## 7. 创作后续意见(面板底部区)
渲染时基于当前进度自动生成,供你参考修改:
- **剧情建议**:下章走向、冲突升级点、伏笔提醒。
- **一致性提醒**:哪些角色久未出场(缺席告警)、哪些伏笔悬置过久。
- **风格反馈**:与 learn-style 风格指纹的漂移度。
- **进化区**(evolve-style 接入):能力曲线、指纹偏差(锁死区/健康区/失控区)、手法掌握度。

## 8. references 索引(全部可达,勿遗漏)

| reference | 讲什么 | 谁调用 |
|---|---|---|
| `power-system.md` | 战力系统/跳级越级校验 | 本文 §3 |
| `foreshadowing-registry.md` | 伏笔分治(源作只读/同人可加/桥接) | 本文 §4.0 |
| `voice-lines.md` | 角色声线库(防说话均质化) | 本文 §5.6 |
| `psychodynamic-char.md` | 心理动力学角色(动机-恐惧矩阵/错误信念/行动化) | 角色卡内核 |
| `relationship-web.md` | 多维关系(11维)+ 冲突网(去二元阵营/去铁板化) | 本文 §5.5 关系网 |
| `information-truth-layer.md` | 隐藏真相层 + 信息溯源 + 秘密状态机 + 暴露度 | 角色卡 POV/秘密 |
| `character-uniqueness.md` | 角色独特性(防脸谱化/对话都一样) | novel-team-composition 反向引 |
| `novel-team-composition.md` | 团队配置查新(反模板) | write-novel quick-skeleton |
| `subtext-dialogue.md` | 对话潜台词(权力博弈/言外之意) | write-romance / write-mystery 跨 skill |
| `genre-knowledge.md` | 题材知识库(写过的世界规则/史料沉淀) | evolve-style 知识积累 |

## 喂给谁 / handoff
- **write-chapter**:每章只注入当前活跃实体(角色卡/伏笔/摘要),低上下文省 token。
- **learn-style**:角色刻画手法参考。
- **write-novel**:设定骨架为创作链提供"基准",意见区反馈迭代。
- **发布导出**:写完章节 → `python3 ~/.claude/skills/build-world/scripts/export_publish.py <项目目录>` → 导出"分卷文件夹→章txt"发布格式(便于观看/发表)。
- 产物:`<项目目录>/`(设定库)+ `panel/index.html`(可视化)+ `发布/`(txt 发布格式)。
