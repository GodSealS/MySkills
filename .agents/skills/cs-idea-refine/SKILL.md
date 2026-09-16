---
name: cs-idea-refine
description: "Refines raw ideas into sharp, actionable concepts through structured divergent and convergent thinking. Use when an idea is still vague, when you need to stress-test assumptions before committing to a plan, or when you want to expand options before converging. / 通过结构化发散与收敛思维将原始想法精炼为可执行概念。用于想法尚模糊、需要压力测试假设或希望在选择前扩展选项时。"
---

# Idea Refine

Refines raw ideas into sharp, actionable concepts worth building through structured divergent and convergent thinking.

## How It Works

0. **Read SysDocs Context:** Establish the project's current capabilities and constraints before expanding the idea.
1. **Understand & Expand (Divergent):** Restate the idea, ask sharpening questions, and generate variations.
2. **Evaluate & Converge:** Cluster ideas, stress-test them, and surface hidden assumptions.
3. **Sharpen & Ship:** Produce a concrete markdown one-pager moving work forward.

## Usage

This skill is primarily an interactive dialogue. Invoke it with an idea, and the agent will guide you through the process.

**Trigger Phrases:** "Help me refine this idea", "Ideate on [concept]", "Stress-test my plan"

## Output

The final output is a markdown one-pager saved to `docs/ideas/[idea-name].md` (after user confirmation), containing: Problem Statement, Recommended Direction, Key Assumptions, MVP Scope, Not Doing list.

## Detailed Instructions

### Philosophy
- Simplicity is the ultimate sophistication. Push toward the simplest version that still solves the real problem.
- Start with the user experience, work backwards to technology.
- Say no to 1,000 things. Focus beats breadth.
- Challenge every assumption. "How it's usually done" is not a reason.

### Phase 0: Read SysDocs Context

Before restating the idea or generating variations, follow `../../references/sysdocs-design-context.md`: read relevant accepted specs/ADRs, use the active layout's navigation and summaries to select affected bodies, and verify key facts with source. Record necessary gaps without forcing full initialization; carry the context summary into the one-pager.

### Phase 1: Understand & Expand (Divergent)

1. **Restate the idea** as a crisp "How Might We" problem statement.
2. **Ask 3-5 sharpening questions**: Who is this for? What does success look like? What are real constraints? What's been tried before? Why now?
3. **Generate 5-8 idea variations** using lenses: Inversion, Constraint removal, Audience shift, Combination, Simplification, 10x version, Expert lens.

### Phase 2: Evaluate & Converge

1. **Cluster** ideas into 2-3 distinct directions.
2. **Stress-test** each against: User value (painkiller or vitamin?), Feasibility (hardest part?), Differentiation (would someone switch?). Ground feasibility in the SysDocs baseline: identify reusable capabilities, affected modules, and proposed boundary or contract changes. Mark directions that depend on unresolved context as provisional.
3. **Surface hidden assumptions**: What you're betting is true, what could kill the idea, what you're choosing to ignore.

Be honest, not supportive. Push back on complexity, question real value.

### Phase 3: Sharpen & Ship

```markdown
# [Idea Name]
## Problem Statement
[One-sentence "How Might We" framing]
## Recommended Direction
[The chosen direction and why — 2-3 paragraphs max]
## System Context
[Documents/sections read, affected modules, capabilities to reuse, constraints and proposed departures; missing/not-applicable baseline and unresolved discrepancies]
## Key Assumptions to Validate
- [ ] [Assumption — how to test it]
## MVP Scope
[Minimum version. What's in, what's out.]
## Not Doing (and Why)
- [Thing] — [reason]
## Open Questions
```

The "Not Doing" list is arguably the most valuable part. Focus is about saying no to good ideas.

## Anti-patterns
- Generating 20+ shallow variations instead of 5-8 considered ones
- Being a yes-machine — push back on weak ideas
- Skipping "who is this for" — every good idea starts with a person
- No assumptions surfaced before committing

## Interaction with Other Skills

- `cs-interview-me`: upstream — extracts what the user actually wants before refining
- `grill-me`: downstream — stress-test the refined concept before writing a spec
- `cs-spec-driven`: downstream — formalize the refined idea into a spec

## Verification

- [ ] One-pager cites the SysDocs baseline or its absence; direction comparisons identify reuse, module impact, and unresolved assumptions
- [ ] A clear "How Might We" problem statement exists
- [ ] Target user and success criteria defined
- [ ] Multiple directions were explored
- [ ] Hidden assumptions explicitly listed
- [ ] A "Not Doing" list makes trade-offs explicit
- [ ] Output is a concrete artifact, not just conversation
- [ ] User confirmed final direction before implementation
