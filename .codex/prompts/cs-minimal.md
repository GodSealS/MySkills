---
description: "Guides minimal-solution selection before writing code: confirm a change is needed, then reuse in-repo code, the standard library, platform-native features, or an installed dependency before writing new implementation. Use when deciding whether to add an implementation, dependency, config option, abstraction, or a second code path; when choosing among reuse, stdlib, native, and dependency options; when retaining a known limitation that needs a recorded upgrade trigger; or when the user asks for a minimal solution or to avoid over-engineering. / 指导写码前的最小解选择：先确认改动是否必要，再依次复用库内代码、标准库、平台原生能力或已有依赖，最后才写新实现。用于决定是否新增实现、依赖、配置项、抽象或第二实现路径时，在复用/标准库/原生/依赖方案之间选择时，保留需记录升级触发条件的已知限制时，或用户要求“最小解”/“避免过度设计”时。"
argument-hint: "[args]"
---

Invoke the cs-minimal skill and follow its workflow for: $ARGUMENTS