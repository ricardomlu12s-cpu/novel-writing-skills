# 题材知识库框架(Genre Knowledge)

题材不限 → 每本书按题材加载**对应知识库**(设定规则/爽点/套路/知识域),专业不泛泛。

## 题材注册表
```json
{"id":"game-novel","name":"网游","traits":["等级/副本/装备/职业/公会"],"knowledge_domains":["游戏机制"],"platform":"番茄优先"}
{"id":"folk-horror","name":"民俗诡异","traits":["戏曲/降神/葬俗/精神病"],"knowledge_domains":["民俗学/民间信仰"],"platform":"起点"}
{"id":"sequence","name":"序列职业","traits":["职业/仪式/序列升级"],"knowledge_domains":["神秘学/符号学"],"platform":"起点"}
{"id":"fourth-calamity","name":"第四天灾","traits":["玩家召集/废土建设/势力扩张"],"knowledge_domains":["游戏设计/策略"],"platform":"起点"}
{"id":"wuxia","name":"武侠","traits":["历史考据/兵器/江湖"],"knowledge_domains":["历史/兵器/江湖文化"],"platform":"起点"}
{"id":"rules-horror","name":"规则怪谈","traits":["规则=可破译实体/智斗求生"],"knowledge_domains":["逻辑学/博弈"],"platform":"番茄"}
```

## 题材知识库目录
```
<项目目录>/genre-knowledge/
├── game-novel.md      # 网游:等级/副本/装备/职业/公会/氪金/开荒/攻略
├── folk-horror.md     # 民俗诡异:戏曲/降神/葬俗/精神病/民间信仰
├── sequence.md        # 序列:职业体系/仪式/升级规则
├── fourth-calamity.md # 第四天灾:玩家召集/废土/建设/势力
├── wuxia.md           # 武侠:历史考据/兵器/江湖规矩
└── rules-horror.md    # 规则怪谈:规则设计/破译逻辑/智斗
```

## 题材知识库内容(每题材)
1. **设定规则**:该题材的核心设定(网游的等级/副本;民俗的仪式/禁忌)。
2. **爽点类型**:该题材的爽点(网游:爆装备/首杀/竞技登顶;民俗:破局/揭秘)。
3. **套路库**:该题材专属套路 + 破局(网游:氪金变强/开荒翻车)。
4. **知识域**:该题材需要的真实知识(民俗学/游戏机制/历史考据)。
5. **开山方向**:该题材"走极端"的方向(genre-innovation 联动)。

## 加载流程
- 开书登记题材 → 题材注册表匹配 → 生成 `genre-knowledge/<题材>.md` 种子。
- 种子可向上吸收:webnovel-writer 37 题材模板 / chinese-webnovel-skills 31 知识库(验证后融合)。
- 创作时按题材注入对应知识库(写网游章注入游戏机制,写民俗章注入民俗学)。

## 与现有衔接
- genre-innovation(开山方向)+ genre-style-matrix(写法基线)+ 本知识库(题材专业)。
- 三件套 = 题材适配的完整闭环。

## 检查清单
- [ ] 题材登记了吗?(注册表)
- [ ] 题材知识库生成了吗?(种子+补全)
- [ ] 创作时注入对应知识域了吗?
- [ ] 多题材融合检查了吗?(anti-sewing-merge 题材版)
