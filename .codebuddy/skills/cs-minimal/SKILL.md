---
name: cs-minimal
description: "Guides minimal-solution selection before writing code: confirm a change is needed, then reuse in-repo code, the standard library, platform-native features, or an installed dependency before writing new implementation. Use when deciding whether to add an implementation, dependency, config option, abstraction, or a second code path; when choosing among reuse, stdlib, native, and dependency options; when retaining a known limitation that needs a recorded upgrade trigger; or when the user asks for a minimal solution or to avoid over-engineering. / 指导写码前的最小解选择：先确认改动是否必要，再依次复用库内代码、标准库、平台原生能力或已有依赖，最后才写新实现。用于决定是否新增实现、依赖、配置项、抽象或第二实现路径时，在复用/标准库/原生/依赖方案之间选择时，保留需记录升级触发条件的已知限制时，或用户要求“最小解”/“避免过度设计”时。"
argument-hint: "[change to implement minimally]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
agent: cs-code-reviewer
---

# Minimal Solution Selection

## Overview

Choose the smallest solution that satisfies correctness, readability, and project conventions — *before* writing code. The goal is to avoid creating anything that does not need to exist: no speculative features, no premature abstractions, no new dependencies a few lines can avoid. Minimal means less code, not a flimsier algorithm or a shorter diff that is wrong.

## When to Use

Apply this skill only when a **selection decision** is on the table:

- Deciding whether to add a new implementation, dependency, config option, abstraction, or a second code path.
- Choosing between in-repo reuse, the standard library, platform-native features, and an installed dependency.
- Retaining a known limitation on purpose, where the upgrade trigger must be recorded.
- The user asks for a "minimal solution", "avoid over-engineering", or "don't add a dependency".

**When NOT to use:** pure execution of an already-decided project pattern, non-coding requests, or test design owned by `cs-tdd`. Explicitly requested features, compatibility guarantees, and implementation constraints still apply.

## The Ladder

Climb the ladder **after** you understand the problem — read the task and the code it touches, trace the real flow end to end, and confirm system constraints first. Stop at the first rung that holds:

| Rung | Question | Result |
|---|---|---|
| 1 | Does this need to exist at all? | If not, say why in one line; create nothing. |
| 2 | Does the codebase already have reusable behavior or a convention? | Reuse it and keep its existing semantics. |
| 3 | Does the standard library do it? | Use the standard library. |
| 4 | Does a native platform feature cover it? | Use the native API, HTML, CSS, or a database constraint. |
| 5 | Does an already-installed dependency solve it? | Use it; do not add a package. |
| 6 | What is the smallest *readable* expression in this project's idiom? | Choose the direct, maintainable implementation. |
| 7 | None of the above applies | Write the smallest new implementation. |

Rung 6 is **not** "make it one line". A one-line nested expression, an implicit side effect, or a trick that strays from project convention is not smaller than a clear multi-line version. Readability wins over line count — see `cs-simplify`.

## Rules

- **Understand before climbing.** Trace the call chain and boundaries first. Search the repository with the retrieval tools available to the project, and record evidence only when the reuse decision actually matters.
- **Bug fix = root cause, not symptom.** List the relevant callers and their contract before editing. Fix at a shared boundary only when the same invariant applies to every affected caller and there is test coverage; otherwise fix at the narrowest boundary that carries the correct semantics. Patching only the path the ticket names leaves sibling callers broken.
- **Respect the test infrastructure.** Follow it when it exists. When `cs-tdd` is active, RED-GREEN-REFACTOR takes full priority; minimalism only removes worthless scaffolding and never limits fixtures, parameterization, or case count.
- **Mark only deliberate ceilings.** Add a `cs-minimal:` marker only when you knowingly retain a limit on scale, concurrency, precision, or behavior. The marker must name the ceiling and an observable upgrade trigger (e.g. `# cs-minimal: global lock; per-account locks if throughput matters`). Ordinary concise code gets no comment.
- **Report only key skips.** Emit `skipped: <content>; revisit when <trigger>` only for decisions like skipping a requirement, choosing reuse, or retaining a limit. Do not append it to every response or every code block.

## Never Simplify Away

Minimalism must not cut any of the following:

- Validation and authorization boundaries for untrusted input.
- Error handling that prevents data loss, corruption, or irreversible side effects.
- Security controls, privacy requirements, access control, and secret protection.
- Accessibility basics, public compatibility promises, and explicit user requests.
- Calibration genuinely required by real hardware, clocks, sensors, or external systems.
- Project-level test requirements for behavior changes and bug fixes.

## Relationship with Other Skills

| Skill | Boundary |
|---|---|
| `cs-incremental` | Owns change *slicing*. Per-slice solution selection may call `cs-minimal` — slice first, then minimize. |
| `cs-simplify` | Owns readability refactoring of *existing* code. Readability and convention win over line count. |
| `cs-tdd` | Owns test strategy and RED-GREEN-REFACTOR. Its test requirements take priority over `cs-minimal`. |
| `cs-code-review` | Remains the only code-review entry point; its Lean pass is the formatted second-axis check. |
| `cs-security` | Still owns threat modeling and guardrails; minimalism never lowers its bar. |


## Red Flags

- The diff adds a config option, interface, or factory that has a single consumer.
- The plan solves a problem that no current code path actually has.
- "I'll abstract it now so we don't have to later" appears in reasoning.
- A new dependency is proposed for something the standard library or platform already does.

## Verification

- [ ] Each rung of the ladder was checked before new implementation was written.
- [ ] No speculative feature, abstraction, or config was introduced without a present consumer.
- [ ] No new dependency was added where reuse, stdlib, native, or an installed package sufficed.
- [ ] Trust-boundary validation, error handling, and test requirements were preserved.
- [ ] Any retained ceiling carries a `cs-minimal:` marker naming the ceiling and upgrade trigger.
- [ ] Key skips are reported as `skipped: <content>; revisit when <trigger>`.

## See Also

- `cs-incremental` — slice changes; minimize inside each slice.
- `cs-simplify` — readability refactor of existing code.
- `cs-tdd` — test-first development.
- `cs-code-review` — the Lean pass reviews for over-engineering.

---

> Adapted from [Ponytail](https://github.com/DietrichGebert/ponytail) (MIT, Copyright (c) 2026 DietrichGebert).
> The minimal-solution ladder, guardrails, and marker convention are derived from Ponytail's ruleset; see `LICENSE` for the full license text.
