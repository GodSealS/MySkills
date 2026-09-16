---
schema: 2
doc_type: architecture
module_id: order
owned_by: mixed
updated: 2026-09-16
source_scope: unversioned
source_paths:
  - src/order/
---

# Order module

## 检索摘要

`OrderService` creates orders and coordinates payment initiation.

## Responsibilities

See the [source index](../../files/order.md), [source entry](../../../src/order/service.py) and [payment flow](../flows/payment.md).

<!-- human:start -->
Keep the accepted ownership rationale intact during migration.
<!-- human:end -->
