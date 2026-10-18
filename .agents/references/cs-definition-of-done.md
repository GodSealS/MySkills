# Definition of Done

> Adapted from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT).

## Per Slice

- Acceptance criteria have observable evidence.
- Behavior changes and bug fixes have appropriate tests; affected checks pass.
- Relevant documentation is synchronized; secrets and unrelated user changes are protected.
- Documentation-only edits use content, link and format verification rather than unrelated application tests.
- Low-impact configuration edits without behavior changes use relevant validators and inspection; behavior-affecting configuration requires appropriate behavior tests.

## Failed Checks and Existing Defects

- Record the failed command/environment, current snapshot and available comparable pre-change results. Diagnose before classifying; an old failure is not automatically unrelated.
- Resolve new/worsened failures and inherited failures affecting the task's required behavior/contracts. Missing evidence or uncertain relevance remains blocking; route decisions beyond the assigned scope to the owner.
- A demonstrated unrelated inherited failure may be recorded separately after required affected checks pass and the assigning lead (or host for ordinary work) accepts the baseline/scope evidence. Record the classification and follow-up owner; this permits scoped completion review, not a waiver of project/team integration or merge gates.
- Preserve the broader command's actual failure, failed/skipped cases and limitations. Never report a failed suite as passing or remove assertions/cases to hide the failure.

## Integration and Final Delivery

- Run project-required regression, build, lint and type checks for executable changes.
  Run them earlier for shared infrastructure changes or uncertain impact.
- Verify changed runtime behavior through suitable tests, browser checks or manual runs.
- Complete review required by the project or owning workflow before merging.
- Reuse passing evidence for unchanged inputs; rerun affected checks after changes or
  failures. A different phase name alone does not require rerunning the same checks.
- Report checks, failures and concrete limitations in the existing task or delivery report.
  Create another checklist artifact only when the workflow actually needs it.
