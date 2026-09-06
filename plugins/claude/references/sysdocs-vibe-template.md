# vibe 临时方案模板（sysdocs-vibe-template）

`SysDocs/VibeCoding/<YYYYMMDD-HHMM>-<slug>[ -N].md` 的生成模板。这是**前置设计**（改代码之前），非事后补录。

## frontmatter（载入即校验）

```yaml
---
schema: 1
doc_type: vibe
vibe_id: <stable-id>
status: draft
updated: <ISO-8601>
targets:
  - module_id: order-service
    sections: [execution-flow, constraints]
implementation:
  status: unknown | code-landed | docs-only-confirmed
  evidence: <git diff | file list | user confirmation>
merge:
  status: pending | merged
---
```

字段约束：

- `vibe_id` 必须是稳定 id。
- `targets[].module_id` 必须精确匹配 manifest；`sections` 使用模板规定的稳定 section ID（如 `design-structure` / `execution-flow` / `class-refs` / `usage` / `constraints`），不使用标题、行号或自由文本猜测。
- 部分初始化且模块尚未修复时允许暂存原始目标，但必须标记 `awaiting-repair`。
- `implementation.status`：`unknown`（未落地）/ `code-landed`（代码已落地）/ `docs-only-confirmed`（用户确认只改文档、代码后补）。
- `implementation.evidence`：code-landed 必须有 git diff、文件清单或用户确认作为 evidence。
- `merge.status`：`pending` / `merged`。

## 1. 设计目标

【人读摘要 ≤5 行】当前设计追求的设计目标。

## 2. 方案与步骤

从结构化内容总结整理：完成目标的具体方案和步骤。

## 3. 调用参数原文 + 审查往返

（放最底，不是整段 chat log）

- **原始参数**（写盘前已脱敏）：<标题 + 结构化内容>
- **架构师缺陷清单**：

| id | level | severity | target | message | resolution |
|---|---|---|---|---|---|
| `F1` | target / step | blocking / warning | `<目标/步骤>` | `<缺陷>` | pending / accepted / fixed |

- **用户对目标级问题的答复**：<明确答复>

> 所有 blocking finding 必须 fixed 或用户明确 accepted，才算无未处理目标级缺陷。原始参数含 token/密码/API key/连接串/私钥时已替换为 `[REDACTED:<类型>]`，不得把秘密复制到本文件、审查往返或日志。

---

## 自检清单（8 条规则）

- [ ] 1. 引用唯一可定位：符号引用反查可命中；匿名结构已豁免
- [ ] 2. 术语唯一：术语只在 `SYSTEM_ROOT.md` §0 定义
- [ ] 3. 数值具体：阈值/超时/重试均写具体值 + 单位
- [ ] 4. 枚举穷举：状态/模式/错误码列全部取值
- [ ] 5. 强度分级：约束用 MUST / MUST NOT / SHOULD / MAY
- [ ] 6. 流程写清参与者
- [ ] 7. 条件写前提与违反行为
- [ ] 8. 本清单逐项打勾
- [ ] `targets[].module_id` 精确匹配 manifest；`sections` 用稳定 section ID
- [ ] 无未处理 blocking 目标级缺陷（fixed 或明确 accepted）
