# Review advisor implementation

Source: `Idea/ponytail-review-advisor-design.md`, including the completed Grill Review.
The user authorized implementation and explicitly prohibited Git commits.

## Ordered tasks

| Task | Primary owner | Depends on | Acceptance and verification |
|---|---|---|---|
| 1. Private review bundle | arch | None | Persona and four protocols trace to the pinned Ponytail source; local references resolve, external allowlist contains only query/docs skills; verify license and provenance. |
| 2. Resource distribution | backend | Task 1 layout | Both builders preserve private bytes and map the advisor model; isolated adapter tests prove public-catalog exclusion and managed-file upgrade protection. |
| 3. Team Build handoff | arch | Tasks 1–2 | Independent first review, advisor recommendations, expert recheck, immediate human blocking dispute, verified repair closure; retain round and expert gates. |
| 4. Team Review handoff | arch | Tasks 1–2 | Preserve schema v1, source IDs, immutable runs and host verdict ownership; validate existing fixtures plus new advice/conflict compatibility cases. |
| 5. Discovery and usage | arch | Tasks 1–4 | Source routers and README describe the new persona and private scope; generated adapters contain it without adding public skills. |
| 6. Integration verification | backend | Tasks 1–5 | Windows/POSIX isolated suites, review validator, source-scope audit and independent review; record unavailable live-host checks explicitly. |

Tasks 1 and 2 can prepare their independent source changes concurrently. Team wiring is
integrated only after the resource contract is checked. Verification checkpoints follow
the private bundle/distribution slice and the final team integration. Existing builder,
installer and validator mechanisms are preferred over new dependencies or schema fields.

## Status

Implementation and required verification completed. All changes remain uncommitted as requested.

## Verification record

| Check | Result |
|---|---|
| PowerShell adapter generation | Passed: 35 public skills, 9 personas; five private resource copies match source bytes. |
| `scripts/test-adapters.ps1` | Passed, including the source-working-tree immutability check and advisor-specific auxiliary roster assertions. |
| `python -B -m unittest discover -s tests -p test_validate_team_review.py` | 34 tests passed; includes role/identity compatibility, accepted-but-unrepaired blockers and immediate pending-human conflict state. |
| `python scripts/validate-team-review.py tests/fixtures/team-review --all` | All 10 fixture expectations passed, including three deliberately invalid fixtures. |
| Private resource safety tests | Both PowerShell and Git Bash cases passed: bundle deletion, malicious manifest and NTFS junction rejection; PowerShell Clean also preserves outside junction targets. |
| Independent review and advisor exercises | Three bounded Codex protocol exercises passed; see `ponytail-advisor-verification.md`. |
| Public-skill scope audit | Only the two team skills changed; no new public skill, private command or other persona roster entry. |
| `scripts/test-adapters.sh` under Git Bash | Passed: all catalog assertions after generation of the harness's 8 public skills and all 9 personas. |
| Real-bundle PowerShell install/upgrade integration | Passed: project/global installs, both builds, rename cleanup, user files and user-edited managed resources preserved. |
| Final real-bundle POSIX install/upgrade integration | Passed: 1 test, 606.253 seconds; two builds and project/global first installs and upgrades, with every command below the unchanged 300-second guard. |

Independent review found manifest-link writes and a Clean compatibility regression; the
implementation now rejects linked ownership paths before access, protects only the agents
subtree during Clean, and retains cleanup for other platform directories. Installer link
checks run before ordinary persona copying. Tests use temporary project and global-install
destinations and do not change the user's installed configuration.

This Windows environment cannot create file symlinks (WinError 1314); junction tests exercise
the reparse-point refusal. Native Linux/macOS and complete live sessions on all four hosts
were not run. Schema tests prove artifact consistency, not actual expert execution or UI dialogs.

POSIX performance regression: the initial real-bundle project upgrade exceeded the
300-second per-command guard in Git Bash. Repeated external `dirname` processes in the
new resource helper were replaced with shell parameter expansion; manifest lookups use
`read` instead of an `awk` process per file. The complete resource fixture and 300-second
guard remain in place. The optimized PowerShell/Git Bash safety suite passed both tests
in 28.199 seconds, with independent confirmation that path checks remain intact.
The optimized complete POSIX integration finished in 606.253 seconds; the previous run
failed after 1267.360 seconds when its project upgrade exceeded the single-command guard.
Both runs used the complete real resource bundle. All independent Required/Critical
findings were closed after fixes and regression verification.

Test entries: `tests/test_advisor_adapters.py` exercises generation, project/global installs,
rename upgrades and preservation of modified user resources; `tests/test_agent_resource_safety.py`
covers deletion, malicious manifests and linked destinations. Shell-specific tests select
available runtimes; both runtimes were available in this Windows verification environment.

## Verified layout adjustment

The installed `@tencent-ai/codebuddy-code` 2.10.0 contains an agent loader that recursively
scans all `.md` files, including documents without persona frontmatter. Executing its
extracted `scanAgentsDirectory` method with an instrumented parse callback selected both
`SKILL.md` and `cs-review-advisor.md`. Renaming the resource to `SKILL.txt` selected only
the persona. Accordingly, the implementation uses the design's section 7.3.6 fallback:
Markdown content in `SKILL.txt` and `PROVENANCE.txt`, with the same private bundle layout.

This is a loader probe, not a full live-host task run. The installed CodeBuddy CLI also
reported a `BaseMarketplace` binding error while printing help. No global configuration
was changed to work around that unrelated startup issue.
