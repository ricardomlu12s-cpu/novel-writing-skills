# 贡献新语言词表（Contribute a Locale）

`remove-ai-tone` 的方法论是语言无关的（7 类 AI 模式、两遍式润色、反净化）。只有词表因语言而异。本文件教你如何为你的语言做一份词表。

The `remove-ai-tone` methodology is language-agnostic. Only the wordlists are per-language. This is how you make one for your language.

## 原理：为什么词表要外置

AI 味分两类：
1. **语言无关的结构问题**（陈述式结论、工整结尾、单线叙事）→ 脚本里的结构扫描 + LLM 兜底，任何语言通用。
2. **语言相关的用词问题**（AI 高频词、弱化副词、万能意象）→ 不同语言完全不同，所以外置成 `locale/<语言>.json`。

## 怎么做一份你的语言词表

### 方法 1：收集（最可靠）

1. 用 GPT/Claude/Gemini 各生成 10 段你语言的小说片段。
2. 用你语言里的人类作者作品做对照。
3. 找出**AI 反复用、人类基本不写**的词和短语。
4. 按下面 7 类归类填入。

### 方法 2：观察模型偏好

- **弱化副词**：AI 爱用"轻微地/轻轻地"这类模糊程度词，人类作家用具体动作。
- **意义膨胀**：AI 爱说"这将是改变一切的时刻"这种大词。
- **万能意象**：AI 爱写"空气仿佛凝固""时间静止"这类空镜头。
- **论文腔**：AI 爱"值得注意的是""综上所述"这类学术连接词。

### 7 类字段说明

| 字段 | 含义 | 例子（英文） |
|---|---|---|
| `ai_only` | AI 专属表达，人类绝不写，最高优先级 | "a testament to", "it was as if" |
| `ai_words` | AI 高频词 | "delve", "tapestry", "moreover" |
| `weak_adv` | 弱化副词泛滥 | "slightly", "gently" |
| `inflate` | 意义膨胀 | "a moment that would change everything" |
| `cliche_conclusion` | 通用结论套话 | "in conclusion", "only time would tell" |
| `paperish` | 论文式段落过渡 | "it is worth noting" |
| `formal` | 正式语体入侵小说 | "furthermore", "hereby" |
| `pacify` / `whitewash` / `harmonize` | 反净化层（化解冲突/洗白/过度圆满） | "forgive and forget" |
| `conflict_signals` / `force_words` | 力度净化检测（冲突信号/直写力度词） | "blood", "scream" |
| `triple_pattern` | 排比三连的正则（适配你的语言标点） | 见 en.json |

## 提交渠道（How to contribute）

1. **Fork 本仓库** → 复制 `remove-ai-tone/locale/en.json` → 改名成你的语言代码（如 `fr.json`、`de.json`、`es.json`、`ko.json`）。
2. **填入词表**（方法见上）。
3. **发 Pull Request**，标题写 `add locale: <语言>`。
4. 我会 review 并合并。合并后所有人都能用你的语言做去 AI 味。

## 语言代码

用 ISO 639-1 两位码：`en` `zh` `ja` `ru` `fr` `de` `es` `ko` `pt` `ar` `it` ...

## 如何本地测试

```bash
# 装好后，用你的语言跑检测（自动识别 --locale）
python3 remove-ai-tone/scripts/detect_aislop.py 你的文本.txt --locale fr
```

## 没有词表时怎么办（空模板也能用）

如果 `locale/<语言>.json` 是空模板（如现在的 `ja.json` / `ru.json`），脚本会：
- 跳过词表检测（该语言无词表），
- **仍然运行语言无关的结构检测**（非人感结构、反净化力度检测）。

也就是说：**没有词表也能用一部分功能，有词表才启用完整检测。**
