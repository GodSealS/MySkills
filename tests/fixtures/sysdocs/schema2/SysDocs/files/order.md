---
schema: 2
doc_type: files
module_id: order
updated: 2026-09-16
source_scope: unversioned
source_paths:
  - src/order/
---

# Order files

## 检索摘要

`OrderService` creates orders; file moves and responsibility changes require updating this index.

## File responsibilities

| 源码路径 | 职责 | 模块 |
|---|---|---|
| `src/order/service.py` | Create orders and coordinate payment. | order |
