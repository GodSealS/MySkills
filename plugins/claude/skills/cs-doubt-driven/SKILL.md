---
name: cs-doubt-driven
description: "Challenge high-risk decisions or consequential assumptions lacking evidence. / 对高风险决策或缺少证据的重要假设进行对抗性验证。"
---

# Doubt-Driven Development

## Scope

Use for security, authorization, payments, destructive migrations, irreversible actions,
or consequential architecture assumptions that current evidence cannot establish.
An ordinary branch change or unfamiliar file alone does not trigger this workflow.
Reuse resolved assumptions when their inputs and constraints have not changed.

## Process

1. **CLAIM:** state the consequential decision and the property that must hold.
2. **EXTRACT:** identify assumptions whose failure would invalidate it.
3. **DOUBT:** seek counterexamples, including failure paths and boundary cases.
4. **RECONCILE:** resolve doubts with source, authoritative documentation or tests.
5. **STOP:** surface unresolved high-risk doubts before dependent action; continue
   independent authorized work. Record evidence in the existing task or decision.

For the highest-stakes unresolved questions, an independent reviewer with focused fresh
context is an optional escalation, not a default review round or required agent.

## Verification

- [ ] Material assumptions have evidence or explicit unresolved risks.
- [ ] Counterexamples and changed inputs were checked.
- [ ] No dependent high-risk action proceeds on an unresolved critical assumption.
- [ ] If an independent review occurred, its material findings were reconciled.
