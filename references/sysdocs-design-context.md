# Task Context from Requirements, Documentation and Source

Shared context protocol for design, implementation and review. Follow [sysdocs-system.md](sysdocs-system.md) for layout, summaries, evidence and protection; do not copy its schema into another workflow.

## Establish task context

1. Resolve the requested project root. An idea without a target project is `not applicable`; never choose another repository. Inventory recognizes schema 2 `SysDocs/README.md`, legacy `SYSTEM_ROOT.md`, partial migration and proposal-only projects.
2. Read the task's relevant accepted specifications and ADRs at their authoritative locations. Then use the project overview, module navigation and header summaries to select architecture, flow and file-index bodies. A legacy manifest remains usable until explicit migration. Do not require reading the entire library or creating one for ordinary design/development.
3. Query a usable project knowledge base through `cs-code-query`, when available. Combine its impact candidates with summary/symbol/business-term search results by **union**, adding changed source and references. Investigate mismatches and verify key facts against source; matching summaries and graphs can both be stale. Missing summaries require body/link fallback. No KB means source-based investigation with an explicit limitation, not automatic initialization or a failed task.
4. For module or responsibility changes, transactions, permissions, data ownership, dependencies or recovery boundaries, read the related flow bodies and constraints even without a direct summary match. If the range cannot be narrowed, read all flow explanations, including embedded or externally maintained ones. Expand reading, not unrelated rewrites; unresolved necessary coverage remains a gap.
5. Record a compact context/impact note in the existing task or review artifact: source scope and revision, documents actually read, relevant modules, semantic changes, candidate differences, constraints, expected documentation changes (or a concrete no-impact reason), checks and gaps. Reuse unchanged evidence; related staged/unstaged/untracked changes invalidate affected conclusions.

## Missing or conflicting context

- **UNINITIALIZED:** continue from task requirements and verified source. A `cs-vibe-coding` proposal may be created without a full library; proposals alone do not initialize project documentation. Only an explicit complete documentation deliverable invokes `cs-sysdocs-init`.
- **PARTIAL-INITIALIZED:** use available relevant evidence; `cs-sysdocs-update` is the maintenance entry. Missing unrelated documents do not block local work. Missing necessary constraints or source evidence must be supplied or marked unresolved before dependent conclusions can pass.
- **Source versus specification:** source describes current behavior; accepted requirements describe intended behavior. Record conflicts and their approved resolution instead of automatically rewriting requirements to match source.
- **Proposals:** describe future changes separately from current architecture. Historical ADR bodies retain their original decisions; use supersession links for changes.
- **Read-only review:** report located findings and missing coverage within assigned artifacts. The host performs authorized document repairs outside the review, then supplies the new snapshot for affected verification. Reading context grants no new write permissions.

## Delivery evidence

Synchronize affected descriptions, summaries, indexes, incoming links and applicable requirements/decisions before fixing the review snapshot. Necessary reversible synchronization is part of an already authorized task. Code and documentation ship in the same change, or the same uncommitted workspace when requested.

Include affected `SysDocs/PROJECT-MAP.md` views when architecture, module execution, interfaces/dependencies or project workflow changes; use the shared protocol's incremental and legacy boundaries for missing maps.

Record structural checks separately from content/source/behavior verification. A structure-only `COMPLETE` result cannot certify documentation meaning. Current-change omissions prevent DONE; unrelated inherited defects are recorded separately. Final synthesis reuses valid slice evidence and checks only new or unresolved impacts. No unconditional full-library refresh or mandatory standalone impact report is required.

For delegated work, supply the project root, task-specific documents or readable snapshots, applicable constraints and known gaps. When complete project documentation is explicitly required, full coverage is its acceptance criterion and cannot be waived using ordinary-task fallback rules.
