# Vibe 前置方案模板（sysdocs-vibe-template）

生成 `SysDocs/VibeCoding/<YYYYMMDD-HHMM>-<slug>[-N].md`；不依赖全库初始化，不补写当前架构。slug 采用小写短横线，拒绝空值、路径分隔符、..、控制字符和 Windows 保留名；同名追加序号。依据 [共享协议](sysdocs-system.md)。

```yaml
---
schema: 2
doc_type: vibe
vibe_id: <稳定 ID>
status: draft
updated: <ISO 日期>
targets: []
implementation:
  status: unknown
  evidence: <已有实现证据，未知则明确写未实施>
merge:
  status: pending
---
```

- targets 可为空；有正式模块时记录 module_id 和本次目标章节，核对旧 manifest 或新模块页；未初始化/归属不明标待定位，不虚构模块。
- implementation.status 为 unknown / code-landed / docs-only-confirmed。code-landed 需要可核实源码/差异；用户确认意图不能替代实际实现证据。
- docs-only-confirmed 仅确认方案或目标规范文档变更，不能因此并入当前架构。merge.status 为 pending / merged；只按实际已吸收范围记录，部分实施保留未实施部分。
- 纯方案不强制 Git/source_scope；记录所参考的事实来源及缺口即可。新符号必须标“拟议”。

```markdown
# <方案标题>

## 检索摘要

- `<现有关键类/结构/实际业务流程>`：<一句话职责及本次影响>。
- 拟议 `<新符号/模块>`：<一句话目标职责，明确尚未实现>。
- 边界：<预期事务、权限、依赖或异常协作变化>。

## 设计目标与当前事实

<区分已核实现状、期望变化、约束及非目标；链接权威规范和 ADR。>

## 方案与步骤

<目标结构、执行顺序、影响范围、兼容/恢复和验收；不能把提案写为当前实现。>

## 文档与实现接入

<预计涉及的说明、文件索引、规范/决策；未有正式库则记录候选归属。>

## 原始输入与评审

- 原始参数：<脱敏后的必要原文，不存整段聊天>。
- 评审来源与状态：<实际完成/不可用；不伪造评审>。

| ID | 目标/步骤 | 严重度 | 问题 | 处理及证据 |
|---|---|---|---|---|
| F1 | <位置> | blocking/warning | <问题> | <待处理/明确接受/已修复依据> |

## 实施及吸收记录

<已落实部分及证据、吸收目标链接、未实施部分；未知就保持 pending。>
```

验证：目标和步骤清楚、摘要区分现有与拟议符号；无秘密；未处理 blocking 问题明确保留；目标存在或诚实待定位；方案不改变项目三态、不冒充当前架构。源码已落实且核实后才在 update 中同步已实现事实，历史方案保留。
