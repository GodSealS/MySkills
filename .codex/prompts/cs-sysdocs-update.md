---
description: "The single maintenance entry for a SysDocs documentation library: repair (partial-initialized), incremental (initialized, refresh drifted modules + merge vibe docs), and rebuild-boundaries (boundary review gate). Runs schema migration, symbol reverse-lookup, drift refresh, vibe four-condition merge, and the shared validator. Use for any update after the project is PARTIAL-INITIALIZED or INITIALIZED. Never calls back into init. / SysDocs 文档库的唯一维护入口：repair（部分初始化）、incremental（已初始化，刷新漂移模块 + 并入 vibe）、rebuild-boundaries（边界复审门控）。执行 schema 迁移、符号反查、漂移刷新、vibe 四条件并入与统一 validator。用于项目处于「部分初始化」或「已初始化」之后的任何更新。绝不回调 init。"
argument-hint: "[args]"
---

Invoke the cs-sysdocs-update skill and follow its workflow for: $ARGUMENTS