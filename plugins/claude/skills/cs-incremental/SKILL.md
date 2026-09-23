---
name: cs-incremental
description: "Deliver multi-step changes in independently verifiable vertical slices. / 将多步骤变更按可独立验证的垂直切片交付。"
---

# Incremental Implementation

## Process

1. Reuse current requirements and tasks. Handle an obvious local change directly;
   otherwise choose the next complete end-to-end outcome in dependency order.
2. Read relevant source and follow the
   [task-context protocol](../../references/sysdocs-design-context.md). Reuse valid
   evidence; update affected documentation or record a concrete no-impact reason.
   Missing documentation does not force library initialization.
3. The host implements ordinary slices. Delegate only a concrete independent subtask
   that benefits from specialist work or when an explicit team workflow requires it.
   Owner tags identify responsibility, not a mandatory new agent. Pass focused context;
   personas never invoke other personas.
4. Implement one coherent outcome. Apply `cs-minimal` when choosing a new solution and
   `cs-tdd` for executable behavior changes and bug fixes. Deliver independent contracts
   before consumers; keep other cross-domain slices end-to-end.
5. Run tests/checks affected by the slice, then verify its acceptance criteria. Apply
   [Definition of Done](../../references/cs-definition-of-done.md) at integration/final
   delivery. Shared infrastructure changes or uncertain impact can require full regression
   earlier. Reuse passing checks for unchanged inputs.
6. Update task status and evidence. Commit coherent validated increments when requested
   or established by project workflow; otherwise deliver workspace changes. Continue
   within authorized scope, stopping at actual blockers or requested checkpoints.

## Boundaries

- Touch only requested scope; keep each increment independently revertible.
- Keep the application buildable; use flags when incomplete work must be merged.
- Preserve user changes and security, compatibility and accessibility requirements.
- Diagnose failed checks; new changes invalidate affected earlier evidence.

## Verification

- [ ] Each slice has a complete outcome and appropriate passing checks.
- [ ] Required integration/final checks pass for the delivered snapshot.
- [ ] Behavior and affected documentation agree; unresolved gaps are reported.
- [ ] Task status and evidence are current; user changes remain intact.
- [ ] Commit or workspace delivery matches user intent and project workflow.

Use UI, API, browser or test skills only when that work is in scope. Team workflows retain
their explicit ownership and review contracts.
