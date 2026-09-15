# SysDocs Context Before Design

Shared read-only context protocol for `cs-interview-me`, `cs-idea-refine`, `cs-api-design`, and `cs-vibe-coding`. Complete it before forming project-specific hypotheses, evaluating directions, or drafting contracts and steps.

## Read and establish the baseline

1. Resolve the target project root from the user's instruction, otherwise use the current workspace root. Inspect that project's `SysDocs/`; use [sysdocs-system.md](sysdocs-system.md) §§1–2 for root boundaries and the three-state inventory. For an idea with no target project, record `not applicable` and continue without selecting an unrelated repository.
2. Read `SysDocs/SYSTEM_ROOT.md` first when available. Follow its module manifest to the affected module documents and registered pages, then relevant specifications and ADRs. Read enough to identify existing capabilities, responsibilities, dependency direction, public contracts, data flows, and binding constraints for this task.
3. Record a compact context summary: project root and inventory state; document paths and sections actually read; affected module IDs; relevant facts and constraints; missing, stale, or conflicting information. Distinguish documented current behavior, the user's requested changes, and assumptions requiring verification. An unchanged baseline already read in this session may be reused with its references.

## Missing or conflicting context

- **UNINITIALIZED:** Interview, idea refinement, and API design may continue from the user's requirements and available specifications/code, explicitly labeling the missing SysDocs baseline and provisional conclusions. Reading context does not authorize creating a documentation library. `cs-vibe-coding` retains its rejection gate and requires `cs-sysdocs-init` first.
- **PARTIAL-INITIALIZED:** Read the available system documents and record missing or inconsistent manifest entries. Use `cs-sysdocs-update` repair as the maintenance route; this context step does not repair documents. Vibe drafts may preserve unresolved targets as `awaiting-repair` under their existing template rules.
- **Stale or conflicting evidence:** Verify only the relevant claims against available source/contracts and user clarification. Record the discrepancy and its effect on the proposal. Keep dependent decisions provisional while continuing unaffected work. Knowledge graphs can locate evidence; summaries and graphs do not replace reading available system documents.
- **Requested design changes:** Treat SysDocs as the baseline for understanding the current system. Describe proposed departures and their impact explicitly; apply the calling skill's existing decision gates when resolving constraints or changing user goals.

## Completion evidence

Include the context summary in the calling skill's existing conversation or output artifact, with references supporting the proposed direction. State `not applicable`, unavailable evidence, and unresolved assumptions honestly. When delegating design work, supply the project root, document paths (or readable snapshots), relevant constraints, and gaps; the recipient reads the relevant documents before judging the proposal. This protocol grants no additional writes or initialization/update actions.
