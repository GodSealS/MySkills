# Evidence and measurement for Team Refactor

Read when classifying findings, comparing current source with requirements, or handling `performance` / `both` focus. Preserve source paths, versions and measurement artifacts; never turn a proposal into a result.

## Finding record

For each stable `F-NNN`, record type (`structure`, `performance`, or `causal hypothesis`), source locator, business path and contract, observation, impact, evidence and its source/scope/version, causal explanation, expert confirmation (`confirmed | rejected | unverified`) and plan decision (`planned | deferred | no-change | needs-measurement`). Severity and implementation priority are separate. Rejection needs evidence that the **finding** is false; rejecting a fix does not reject the finding.

Evidence types can coexist within one finding:

| Type | Supports | Does not support by itself |
|---|---|---|
| `measured` | A result under a recorded workload/environment | Different traffic, hardware or future improvement |
| `source-confirmed` | Current source/config behavior at the recorded revision | Approved intended requirement |
| `requirement-confirmed` | Effective requirement or accepted decision | Current implementation compliance |
| `hypothesis` | A question and a way to test it | A claimed root cause or benefit |

When source conflicts with an effective spec, record current behavior, expected behavior, impact and the authority for resolving the difference side by side. Do not promise to preserve a known defect merely because it exists, and do not silently rewrite a requirement to match code. A dependent plan is not `READY` until the conflict has an approved repair, requirement change, or compatibility arrangement.

SysDocs structural `COMPLETE` attests only to the checked structure. Verify summaries, bodies, symbols, flows and constraints separately against current source/config, behavior tests or review evidence. If symbol or Mermaid parsing was unavailable, record that limit. Missing SysDocs or KB alone does not block a conclusion when other necessary evidence is sufficient.

## Performance baseline

For every measurement record: input snapshot, environment/hardware/resources, runtime version, data volume, business workload, concurrency, hot/cold state, warm-up, repetition count, sampling window, metric/unit/statistic, command or collection method, time and raw artifact path. Use project-appropriate metrics: API latency distribution, throughput, query counts/duration, CPU/memory, build time or browser load/interaction. Do not invent percentiles from static inspection or compare unlike environments as proof of improvement. Record inadequate sample sizes.

Derive acceptance from the user's goal, an existing SLO/budget or a clearly labeled proposed goal. Include guard metrics such as error rate, consistency and resource cost, and a decision rule that accounts for measurement variation. When the baseline is absent, first task is a feasible profile/trace/benchmark design: workload, environment, repetitions, tool, raw output, comparison and decision rule. Mark the production optimization as dependent research, not executable implementation. Check official sources before adopting framework-specific tools, standards or thresholds; no universal threshold is built into this skill.

Run only already existing measurements in a known, authorized isolated environment and record the real command and result. If the run would alter data or generate artifacts, use a disposable copy. If the environment, resource budget or authority is missing, keep the plan and the unknown explicit; do not run production load or incur paid resources by implication.
