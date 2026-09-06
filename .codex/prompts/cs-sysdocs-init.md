---
description: "Generates the SysDocs system documentation set (SYSTEM_ROOT.md + one module doc per module) for a target project in one pass. Use only when the three-state inventory says the project is UNINITIALIZED — no SysDocs/ dir, empty, only VibeCoding/, or no valid SYSTEM_ROOT.md/module docs yet. Never runs re-init or repairs; that is cs-sysdocs-update's job. / 一次性全量生成项目 SysDocs 系统文档（SYSTEM_ROOT.md + 每个模块一份模块文档）。仅当三态清单判定项目为「未初始化」时使用——无 SysDocs/ 目录、为空、只有 VibeCoding/、或尚无有效 SYSTEM_ROOT.md/模块文档。绝不执行 re-init 或 repair，那是 cs-sysdocs-update 的职责。"
argument-hint: "[args]"
---

Invoke the cs-sysdocs-init skill and follow its workflow for: $ARGUMENTS