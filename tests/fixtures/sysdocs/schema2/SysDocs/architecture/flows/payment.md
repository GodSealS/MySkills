---
schema: 2
doc_type: architecture
updated: 2026-09-16
source_scope: unversioned
source_paths:
  - src/order/
---

# Payment flow

## 检索摘要

`OrderService` coordinates payment; changes to transaction ownership require reading the rollback flow.

## Flow

Order creation precedes payment completion. [Order responsibilities](../modules/order.md).
