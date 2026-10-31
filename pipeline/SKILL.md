---
name: pipeline
license: MIT
description: skill工作链条 — 六领域能力的闭环编排枢纽。入口。用户提到"工作链条"/"skill链"/"整个链路"/"端到端跑一遍"或给一个模糊任务不知道归谁时,由本枢纽判断走哪一环。不是独立技术,是路由 + 全链运行手册。
allowed-tools: [Bash, Read, Grep, Write, Edit]
---

# skill工作链条(Skill Work Chain)

六领域能力的**闭环编排枢纽**。它不是独立技术,是路由表 + 全链运行手册。你只管说大白话,它决定走链上哪一环、产出喂给谁。

## 链路图

```
recon-pipeline ──targets.jsonl──▶ 现有攻击skill(api-attacks/sql-injection/jwt-hacking)
     │  └──llm_exposed──▶ llm-red-team ──findings.jsonl──▶ ml-finetune(防御规则+负样本过滤)
     │                                                      │
static-re ──签名/密钥──▶ frida-hooks(动态验证回流)         ├─▶ hallucination-eval(共享契约)
     │                                                      │
token-ops(横切)──批量/缓存审计──▶ ml-finetune批量、llm-red-team批量、deep-research批量
```

- **6 个领域**:① 编程开发(成熟)② AI训练(ml-finetune)③ 渗透+逆向(recon-pipeline + static-re + 现有攻击skill)④ token成本(token-ops)⑤ 幻觉检测(hallucination-eval 内嵌)⑥ AI红队(llm-red-team)。
- **3 个环节技能**:recon-pipeline、static-re、llm-red-team、ml-finetune。
- **1 个横切**:token-ops。
- **2 个共享件**:hallucination-eval(契约)、verifier(幻觉核查段)。
- **闭环接缝**:统一 `## 喂给谁 / handoff` 节 + `.omc/research/<job>/` 产物目录。

## 路由表(大白话 → 走哪一环)

| 用户可能说 | 走链上哪一环 |
|---|---|
| "帮我扫描这个网站/查漏洞/这域名安不安全" | recon-pipeline |
| "看这个 app 干了什么/逆向/反编译/apk" | static-re → frida-hooks |
| "测试这个模型会不会被绕过/越狱测试/提示注入防护" | llm-red-team |
| "想自己训练个模型/微调/训练AI" | ml-finetune |
| "太烧 token 了/怎么省钱/降低成本" | token-ops |
| 模糊任务、不知道归谁 | **本枢纽**判断 → 派发 |

## 全链运行手册(端到端跑一遍)

1. **启动**:确认目标与授权 → `.omc/research/<job>/AUTHORIZATION.md`。
2. **侦察**:recon-pipeline → `targets.jsonl`(标 llm_exposed)。
3. **分流**:
   - 普通目标 → 现有攻击 skill(api-attacks/sql-injection/jwt-hacking)逐点测。
   - `llm_exposed:true` → llm-red-team 做越狱/注入测试 → `findings.jsonl`。
   - 有 app/二进制 → static-re → 签名/密钥 → frida-hooks 动态验证。
4. **训练**:ml-finetune 消费红队防御规则 + 负样本过滤 → 训练 → 评估。
5. **核查**:产物由 verifier 按 hallucination-eval 契约复核(幻觉率)。
6. **降本**:批量任务统一走 token-ops(Batch API + 缓存 + 审计)。

## 边界
- 越狱/渗透仅限自有资产、授权测试、CTF。
- 每环的完整步骤见各自 skill;本枢纽不重复技术细节,只负责串链。
