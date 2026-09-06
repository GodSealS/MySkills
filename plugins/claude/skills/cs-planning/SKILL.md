---
name: cs-planning
description: "Breaks work into ordered tasks. Use when you have a spec or clear requirements and need to break work into implementable tasks. Use when a task feels too large to start, when you need to estimate scope, or when parallel work is possible. / 将工作拆分为有序任务。用于有规范或明确需求、需要估算范围、或并行工作可行时——依赖图、垂直切片、验收标准。"
---

# Planning and Task Breakdown

## Overview

Decompose work into small, verifiable tasks with explicit acceptance criteria. Good task breakdown is the difference between an agent that completes work reliably and one that produces a tangled mess.

## When to Use

- You have a spec and need to break it into implementable units
- A task feels too large or vague to start
- Work needs to be parallelized across multiple agents or sessions
- You need to communicate scope to a human
- The implementation order isn't obvious

**When NOT to use:** Single-file changes with obvious scope, or when the spec already contains well-defined tasks.

## The Planning Process

### Step 1: Enter Plan Mode

Before writing any code, operate in read-only mode:
- Read the spec and relevant codebase sections
- Identify existing patterns and conventions
- Map dependencies between components
- Note risks and unknowns

### Step 2: Identify the Dependency Graph

Map what depends on what. Implementation order follows the dependency graph bottom-up.

**Architect Fan-Out:** After mapping the graph, **FAN-OUT to `cs-architect`** (via `Task`) to validate module boundaries and dependency direction before committing to a task order. The architect confirms there are no cycles and that dependencies flow the right way. If the spec already contains architect-approved ADRs, this step is a confirmation check, not a full redesign.

### Step 3: Slice Vertically

Instead of building all database, then all API, then all UI — build one complete feature path at a time.

**Bad (horizontal slicing):**
```
Task 1: Build entire database schema
Task 2: Build all API endpoints
Task 3: Build all UI components
Task 4: Connect everything
```

**Good (vertical slicing):**
```
Task 1: User can create an account (schema + API + UI)
Task 2: User can log in (auth schema + API + UI)
Task 3: User can create a task (task schema + API + UI)
Task 4: User can view task list (query + API + UI)
```

### Step 4: Write Tasks

```markdown
## Task [N]: [Short descriptive title]

**Description:** One paragraph explaining what this task accomplishes.

**Primary owner:** [arch | frontend | backend]   ← required; routes the task to one domain lead
**Collaborators:** [none | arch | frontend | backend]   ← optional; consulted only where the slice crosses their boundary

**Acceptance criteria:**
- [ ] [Specific, testable condition]
- [ ] [Specific, testable condition]

**Verification:**
- [ ] Tests pass: `npm test -- --grep "feature-name"`
- [ ] Build succeeds: `npm run build`
- [ ] Manual check: [description]

**Dependencies:** [Task numbers or "None"]
**Files likely touched:** [File paths]
**Estimated scope:** [Small: 1-2 files | Medium: 3-5 files | Large: 5+ files]
```

**Ownership rules:**
- `frontend` → UI structure, components, state, browser behavior → `cs-frontend-lead` in BUILD
- `backend` → API, data layer, server logic → `cs-backend-lead` in BUILD
- `arch` → public contracts, module skeletons, cross-cutting config (structural artifacts only, not business features) → `cs-architect` in BUILD
- Keep a cross-domain feature as one end-to-end vertical slice. Give it one primary owner and list the other domain as a collaborator. Split out a backend contract task only when it is independently versioned, shared, or needed before parallel frontend work; order that contract before its consumer.

### Step 5: Order and Checkpoint

Arrange tasks so dependencies are satisfied and verification checkpoints occur every 2-3 tasks.

## Task Sizing Guidelines

| Size | Files | Scope | Example |
|------|-------|-------|---------|
| **XS** | 1 | Single function or config | Add a validation rule |
| **S** | 1-2 | One component or endpoint | Add a new API endpoint |
| **M** | 3-5 | One feature slice | User registration flow |
| **L** | 5-8 | Multi-component feature | Search with filtering |
| **XL** | 8+ | **Too large — break it down** | — |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll figure it out as I go" | That's how you get a tangled mess. 10 minutes of planning saves hours. |
| "The tasks are obvious" | Write them down anyway. Explicit tasks surface hidden dependencies. |
| "Planning is overhead" | Planning IS the task. Implementation without a plan is just typing. |

## Verification

- [ ] The source spec contains a completed `## Grill Review` decision or explicit skip with accepted risks
- [ ] Architecture fan-out to `cs-architect` validated the dependency graph (or spec ADRs reviewed)
- [ ] Every task has acceptance criteria
- [ ] Every task has a verification step
- [ ] Every task has a primary owner (`arch` / `frontend` / `backend`)
- [ ] Task dependencies are identified and ordered
- [ ] No task touches more than ~5 files
- [ ] Checkpoints exist between major phases
- [ ] The human has reviewed and approved the plan

## Interaction with Other Skills

- `cs-spec-driven`: upstream — provides the spec to break into tasks
- `cs-architect` (agent): fan-out to validate dependency graph and module boundaries before ordering tasks
- `grill-me`: upstream — stress-test the design before committing to a task plan
- `cs-incremental`: downstream — execute tasks in thin vertical slices, routed by owner
- `cs-frontend-lead` / `cs-backend-lead` (agents): downstream — implement primary-owner tasks and consult on listed collaborator boundaries
- `cs-tdd`: downstream — test-driven implementation of individual tasks
- `cs-sysdocs-update` / `SysDocs/`: when a `SysDocs/` library exists, derive task boundaries from its module manifest + dependency direction instead of re-guessing from source

## See Also

See `../../references/cs-definition-of-done.md` for the project-wide bar every task clears.
