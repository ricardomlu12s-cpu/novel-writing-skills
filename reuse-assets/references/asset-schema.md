# 资产 Schema 与标签规范

定义全局资产库里每类资产的文件格式与标签字段。**对齐现链 schema,不另造格式**,让检索/注入/连续性校验都能直接消费。

## 通用标签(每个资产文件顶部 YAML frontmatter)

```yaml
---
source_book: <拆自哪部作品 | 自研>
dimension: <风格 | 手法 | 情节 | 世界观 | 角色>
granularity: <骨架 | 细节>
tags: [<自由标签>]
---
```

字段含义:
- `source_book`: 资产来源。原创自研的填 `自研`。
- `dimension`: 五维之一,决定"写什么场景时注入它"。
- `granularity`: **防串味核心分界**。
  - `骨架`: 去细节的结构(如"身份错位→责任觉醒"),可跨书安全复用。
  - `细节`: 具体台词/设定名/角色声线,仅限同源书使用,否则串味。
- `tags`: 检索用自由标签(题材/情绪/类型关键词)。

## 各库 schema

### ① deconstruction/(拆书产物)
- 直接是 study-book 的 `source-canon/` 完整目录。
- 额外加一个 `asset.json`(标签清单):
```json
{
  "source_book": "诡秘之主",
  "dimensions_available": ["世界观", "角色", "情节", "风格"],
  "granularity": "骨架",   // 拆书产物默认"骨架"(可复用);细节在源作文本里,不复制
  "tags": ["诡异", "序列", "低魔"],
  "characters_count": 12,
  "foreshadowing_count": 30
}
```

### ② style/(风格指纹)
- 即 learn-style 的 `fingerprint.md`,顶部加通用标签。
- 默认 `granularity:骨架`(手法可复用);具体"台词/口头禅"属细节,标在文件内"规避"区。

### ③ technique/(写作手法)
```markdown
---
source_book: 自研
dimension: 手法
granularity: 骨架
tags: [白金手法, 反套路]
---
# 手法: <名>
## 定义
<一句话>
## 适用场景
<什么时候用>
## 反例(过度使用)
<什么时候别用>
```

### ④ plot/(情节模式)
```markdown
---
source_book: 自研
dimension: 情节
granularity: 骨架
tags: [钩子, 反转]
---
# 情节模式: <名>
## 结构骨架
<欲望 → 障碍 → 蓄势 → 释放 的四拍>
## 变体
<这个骨架的 3 种新写法>
## 易被猜中的版本(规避)
<读者一看就猜到的老套路>
```

### ⑤ knowledge/(世界知识)
```markdown
---
source_book: 自研
dimension: 世界观
granularity: 骨架
tags: [历史, 中世纪]
---
# 知识: <领域>
<写过的世界规则/史料/题材沉淀>
```

## 引用不复制(asset-refs.json)

项目根放一个引用清单,只存指针:
```json
[
  {"dimension":"世界观","source_book":"诡秘之主","asset":"deconstruction/诡秘之主/source-canon","use_as":"世界框架底盘"},
  {"dimension":"风格","source_book":"龙族江南文风","asset":"style/龙族江南文风","use_as":"全书基调"}
]
```
- 项目**不拷贝**资产内容,写章时按指针去全局库取。
- `use_as` 说明这件资产在本书里的用途(对应配方层)。

## 防串味三闸(与 SKILL.md 一致)

1. **来源隔离**: 注入只取配方点名的 `source_book`。
2. **粒度分界**: `骨架` 可跨书,`细节` 仅同源。
3. **维度分层**: 按 `dimension` 分层注入,不混合。
