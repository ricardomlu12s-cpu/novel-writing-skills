# novel-writing-skills

> 语言 / Languages: [中文](README.md) · [English](README.en.md)

写中文长篇小说的工具。拆书、建设定、写章节、去 AI 味、查前后矛盾，这些事拆成一个个独立模块，想用哪个用哪个。

> 面向中文写作。去 AI 味的词表以中文为主（英文也带了，其他语言留了模板，自己填词表就能用）。不挑 AI：Claude、GPT、Gemini、通义、豆包这些都能用，命令行或 API 也行。见下文「不挑 AI」。

## 有哪些模块

| 模块 | 干什么 | 什么时候用 |
|---|---|---|
| `write-novel` | 入口，把你说的需求分到对的模块 | 说「写小说」、需求模糊时 |
| `study-book` | 拆一部作品，产出设定库 | 写同人、想学一部作品 |
| `build-world` | 世界观、角色卡、伏笔表、看板 | 建设定、写角色、查伏笔 |
| `write-chapter` | 分层摘要 + 正典账本 + 查矛盾 | 写第几章、接着写 |
| `remove-ai-tone` | 去 AI 味、标点统一 | 觉得「不像人写的」 |
| `plan-plot` | 反套路、高潮节奏、常识、打斗 | 情节老套、卡文、写打斗 |
| `write-romance` | 感情线 | 写 CP、感情戏 |
| `write-mystery` | 推理、线索账本、公平竞赛 | 写智斗、悬疑 |
| `adapt-platform` | 起点/番茄风格、群像 | 选平台、写群像 |
| `apply-feedback` | 读者意见分档修改 | 按读者意见改章节 |
| `evolve-style` | 风格进化、防写死、能力记录 | 该总结了、风格漂了 |
| `publish-book` | 发布前检查、排版导出 | 发布、上架 |
| `learn-style` | 学一部作品的文风 | 吸收风格、仿写不照搬 |
| `reuse-assets` | 全局资产库，拆一次多本书用 | 跨书复用、防串味 |
| `ideate` | 骨架化 + 跨领域联想 + 张力检查 | 没新意、剧情被猜到 |
| `pipeline` | 技术类任务的入口（不写小说可以忽略） | 非创作类闭环 |

## 安装

```bash
git clone https://github.com/ricardomlu12s-cpu/novel-writing-skills.git
cd novel-writing-skills
python3 install.py          # 会问你要英文/中文/日文/俄文界面
```

装完重启，说触发词（比如「写小说」）或 `/模块名`。

跨平台安装、更新、卸载见 [DEPLOYMENT.md](DEPLOYMENT.md)。

## 需要什么

- 脚本要 **Python 3.8+**，只用标准库，不用装别的（`ideate` 的图模式可选 `networkx`，不装也能用）。
- `SKILL.md` 和 `references/` 就是 markdown 说明，AI 直接读，没有 Python 也能用。脚本是锦上添花的「确定性检查」，不是必须。

## 不挑 AI

模块就是「一个目录 + 一份说明 + 几个脚本」，不绑死某一家：

| 用法 | 怎么做 |
|---|---|
| Claude Code | `/模块名` 或说触发词 |
| 其他带 skills 目录的客户端 | 把目录丢进去，或 `install.py --dir` 指定 |
| 命令行直接用（不经过 AI） | 单独跑脚本：`python3 write-chapter/scripts/continuity_check.py <项目>` |
| 接 API 自己写流程 | 把 SKILL.md 当提示词模板，脚本当工具调，逻辑是纯 markdown + python |

## 项目长什么样

一部小说 = 一个项目目录：

```
<项目>/
├── manuscripts/        正文
├── drafts/             AI 草稿，和正文分开
├── summaries/          分层摘要 L1-L5
├── canon-ledger/       正典账本（facts/promises/timeline，只追加）
├── characters/         角色卡
├── foreshadowing.jsonl 伏笔表
├── relationships.jsonl 关系网
└── ...
```

全局资产（拆书产物、风格库）默认放 `~/.omc/assets/`，用 `ASSET_ROOT` 改位置。

## 为什么这么设计

长篇写着写着容易出的三个毛病，各有一个模块对付：

- **前后矛盾、设定忘了** → 正典账本只追加不改 + 分层摘要冻结 + `continuity_check.py` 硬扫。
- **越写越套路** → `ideate` 把情节压成「骨架」再跨领域嫁接，不是抄细节。
- **越写越贵** → 分层摘要 + `lorebook.py` 按需取 + `context_budget.py` 写前卡额度，单章成本不随篇幅涨。

## 其他

- 这是个人写作练出来的工具，不是官方项目，不保证适合所有人。
- 拆书只学手法，不搬设定名和台词。
- MIT 协议，随便用，商用也行，留个版权声明。

## License

MIT
