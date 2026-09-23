# Definition of Done

> Adapted from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT).

## Per Slice

- Acceptance criteria have observable evidence.
- Behavior changes and bug fixes have appropriate tests; affected checks pass.
- Relevant documentation is synchronized; secrets and unrelated user changes are protected.
- Documentation-only edits use content, link and format verification rather than unrelated application tests.

## Integration and Final Delivery

- Run project-required regression, build, lint and type checks for executable changes.
  Run them earlier for shared infrastructure changes or uncertain impact.
- Verify changed runtime behavior through suitable tests, browser checks or manual runs.
- Complete review required by the project or owning workflow before merging.
- Reuse passing evidence for unchanged inputs; rerun affected checks after changes or
  failures. A different phase name alone does not require rerunning the same checks.
- Report checks, failures and concrete limitations in the existing task or delivery report.
  Create another checklist artifact only when the workflow actually needs it.
