---
schema: 2
doc_type: architecture
updated: 2026-09-23
source_scope: unversioned
source_paths:
  - src/order/
---

# Project map

## 检索摘要

`OrderService.create` returns the pending state. The fixture has one source module.

## 当前项目架构图

```mermaid
flowchart LR
    subgraph order[Order module]
        service[OrderService]
    end
```

[Module responsibilities](architecture/modules/order.md).

## 模块执行流程图

```mermaid
flowchart LR
    create[OrderService.create] --> pending[Return pending]
```

[Source](../src/order/service.py), entry `OrderService.create`.

## 模块关系图

```mermaid
flowchart LR
    order[Order module: no external module dependency in source]
```

No cross-module edge exists in this fixture's source.

## 项目工作流

Not applicable: this fixture has no project automation or documented delivery workflow.
