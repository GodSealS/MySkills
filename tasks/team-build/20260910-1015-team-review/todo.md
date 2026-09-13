# Todo: `cs-team-review` implementation

Checkpoint: **修复批次已完成本地 validator/fixture/adapter 验收**（2026-09-13）。

| Task | Owner | Dependencies | Status | Rounds | Verification handoff |
|---|---|---|---|---:|---|
| T01 Canonical orchestration skill | arch | — | DONE | 1 | `SKILL.md` contract + skill review |
| T02 Schema validator and contract fixtures | backend | — | DONE | 2 | 31 focused validator tests + expected-invalid fixtures |
| T03 CodeBuddy command surface | arch | T01 | DONE | 1 | command adapter equality |
| T04 Router integration | arch | T01, T03 | DONE | 1 | router trigger scan |
| T05 Skill cross-reference integration | arch | T01, T03 | DONE | 1 | stale-reference/serializer scan |
| T06 Core persona roster and read-only boundaries | arch | T01 | DONE | 1 | four-persona roster scan |
| T07 Specialist persona roster and read-only boundaries | arch | T01 | DONE | 1 | three-persona roster scan |
| T08 Adapter builder and conformance tests | arch | T01, T03-T07 | DONE | 1 | Windows adapter test passed; POSIX deferred by host |
| T09 End-to-end and failure fixtures | backend | T01, T02 | DONE | 2 | 7 valid + 3 expected-invalid fixtures via `--all` |
| T10 Build and verification checkpoint | arch | T02, T08, T09 | DONE | 2 | exact Windows/local results in test-report |
| T11 Skill quality review and synthesis | arch | T01-T10 | PARTIAL | 2 | report corrected; independent runtime orchestration review remains open |

## Open runtime verification

- [ ] Real exclusive lock acquisition/competition and crash cleanup.
- [ ] Atomic artifact writes and partial-write recovery.
- [ ] Resume fencing: completed stages are not repeated and drift invalidates confirmations.
- [ ] Runtime Git HEAD/patch/dirty allowlist capture.
- [ ] Real multi-Agent fan-out and handoff integration run.
- [ ] POSIX `sh scripts/test-adapters.sh` on a POSIX-capable host.

## Scope note

Static fixtures prove artifact contract validation only. They do not prove runtime isolation, concurrency, atomicity, resume semantics, or orchestration.
