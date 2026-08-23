---
name: cs-skill-review
model: sonnet
description: 审查一个 skill 的可预测性——按调用、信息层级、粒度、修剪、引导词、失败模式六轴诊断。Use when reviewing a skill, auditing skill quality, checking if a skill follows best practices, or when asked to evaluate a SKILL.md.
---

# Skill Review

Read the target skill's `SKILL.md` and any disclosed reference files, then run this review. Every finding traces to a principle in [`writing-great-skills`](F:\Tools\skills\skills\productivity\writing-great-skills\SKILL.md); when in doubt, consult it.

## Step 1 — Invocation Axis

Check the skill's invocation decision:

- **Model-invoked** (no `disable-model-invocation`): Does the description front-load the skill's **leading word**? Are the **branches** listed — one trigger per genuinely distinct branch, no synonym-duplication? Does another skill legitimately need to reach this one, or could it be user-invoked and pay zero **context load**?
- **User-invoked** (`disable-model-invocation: true`): Is this a skill the agent never needs to fire autonomously? If user-invoked skills multiply, is there a **router skill** to cure **cognitive load**?

Findings: tag each as `invocation-fit` or `invocation-misfit`, with the fix.

## Step 2 — Information Hierarchy Check

Map the skill's content onto the ladder:

1. **Steps** — ordered actions with **completion criteria**. For each step, judge the criterion: is it _checkable_ (agent can tell done from not-done)? Is it _exhaustive_ where it matters ("every rule applied" vs "produce a summary")?
2. **In-skill reference** — definitions, rules, facts. Is it **co-located** (a concept's definition, rules, caveats under one heading)?
3. **External reference** — material behind a **context pointer**. Does the pointer's _wording_ reliably fire when the agent needs the material? Is must-have reference inlined rather than behind an unreliable pointer?

For each rung, ask: is this material at the right rung? Material every **branch** needs → inline. Material only some branches reach → disclose.

Findings: tag `hierarchy-ok` or `hierarchy-shift` (too high / too low), with the target rung.

## Step 3 — Granularity Check

Should this be one skill or more?

- **By invocation**: Is there a distinct **leading word** that should trigger a separate model-invoked skill — a trigger the user actually uses?
- **By sequence**: Do visible **post-completion steps** tempt **premature completion** of the current step? Only split here when the criterion is irreducibly fuzzy _and_ you observe the rush across runs.

Findings: tag `granularity-ok`, `should-split-by-invocation`, or `should-split-by-sequence`.

## Step 4 — Pruning Audit

Run four checks, sentence by sentence:

1. **Single source of truth**: Does each meaning appear in exactly one place? Flag **duplication** — same meaning repeated.
2. **Relevance**: Does each line still bear on what the skill does? Flag **sediment** — stale layers from accumulation.
3. **No-op test**: Does each line change behaviour versus the model's default? A line can be relevant and still be a no-op.
4. **Negation check**: Any prohibitions ("don't X", "never Y")? If so, can they be rewritten as **positive** targets? Flag negations that lack a paired positive instruction.

Findings: tag each as `pruning-ok`, `duplication`, `sediment`, `no-op`, or `negation`. Specify the offending line.

## Step 5 — Leading Words Audit

Identify every **leading word** in the skill — compact pretrained concepts that anchor behaviour (e.g., _relentless_, _tracer bullet_, _lesson_). For each:

- Does the word actually recruit a useful prior from the model? A weak word (_be thorough_) that the model already defaults to is a **no-op** — the fix is a stronger word (_relentless_), not a different technique.
- Does the word appear in both the body (anchoring execution) _and_ the description (anchoring invocation)?
- Are there passages spelling out a concept that a single leading word could **collapse** into one token? ("fast, deterministic, low-overhead" → _tight_)

Findings: list existing leading words with `effective` or `weak` verdict. List missed opportunities: passages that should collapse into a leading word.

## Step 6 — Failure Mode Sweep

Run the six failure modes as a final sweep. The earlier steps should have caught most of these already; this is a last-pass safety net:

| Failure Mode | Symptom | Fix (in order) |
|---|---|---|
| **Premature completion** | Step ends before genuinely done | Sharpen completion criterion first; split sequence only if fuzzy + observed |
| **Duplication** | Same meaning in >1 place | Consolidate to single source of truth |
| **Sediment** | Stale layers, never pruned | Delete irrelevant lines |
| **Sprawl** | Too long even when all-live | Disclose reference; split by branch or sequence |
| **No-op** | Line doesn't change default behaviour | Delete or strengthen (stronger leading word) |
| **Negation** | Prohibition that names the banned thing | Rephrase as positive target; keep only as hard guardrail + pair with positive |

## Output

Produce a review report:

```
## Skill Review: <skill-name>

### Summary
One-line verdict. Key strength + key risk.

### Invocation
- [fit/misfit] finding → fix

### Information Hierarchy
- [ok/shift] finding → target rung

### Granularity
- [ok/split] finding → action

### Pruning
- [type] line → fix (repeat per finding)

### Leading Words
- effective: word1, word2
- weak: word3 → stronger alternative
- missed: "passage text" → leading_word

### Failure Mode Sweep
- [mode] finding → fix (only if not already covered above)
```

Keep the report tight. Every fix traces to a principle. A clean skill with no findings is a valid result — don't invent problems.
