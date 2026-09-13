# Test Report: `cs-team-review` 修复后

日期：2026-09-13

## 验证结果

| 验证项 | 结果 |
|---|---|
| `python -m pytest -q tests/test_validate_team_review.py` | **31 passed** |
| `python -m pytest -q` | **31 passed** |
| `python scripts/validate-team-review.py tests/fixtures/team-review --all` | **通过，exit 0**；7 个 expected-valid fixture 通过，3 个 expected-invalid fixture 按声明错误通过 |
| `python C:\Users\admin\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents/skills/cs-team-review` | **Skill is valid** |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test-adapters.ps1` | **通过** |
| `git diff --check` | 通过；仅报告既有的 LF/CRLF normalization warning |
| `sh scripts/test-adapters.sh` | 未执行；当前 Windows 环境没有可用 POSIX `sh` |

## 已修复并覆盖

- 正例 `complete/code/design/mixed` 的 manifest 文件集合、SHA-256、portable mtime 语义已一致；删除了未列入 manifest 的 stray fixture 文件。
- `case.json` 现在强制声明 `expected_valid`、`expected_status`；expected-invalid 必须声明非空 `expected_error`。
- `--all` 会执行 expected-invalid 断言；单 fixture 默认入口不会把“预期失败”伪装成通过。
- `manifest-drift`、`unauthorized-write`、`reject-confirm` 已改成真实可触发的负例，而不是空壳 blocked 目录。
- validator 检查 review type、finding source/ID、code/mixed Phase 0、manifest allowlist、JSON lock、block reason、conflicting decisions 和 complete-state gates。
- mixed findings 允许同一 fingerprint 合并后保留 code/design 双 source；空 findings 仍可表达无发现的合法 complete run。
- installer/adapter 不再被错误要求携带 repository-local validator；adapter 验证只验证生成的 skill/command 树。

## 尚未被这些测试证明

这些是 host/orchestrator runtime 责任，静态 validator 和 fixture 不足以证明：

- 真正的独占锁竞争、进程崩溃后的锁清理和并发 race；
- atomic write / partial artifact recovery；
- resume 时已完成 stage 不重复执行、target drift 使 confirmation 失效；
- 运行时真实 Git `HEAD`、patch 内容/行数采集；
- 实际 worktree/sandbox 隔离和多 Agent fan-out/orchestration；
- POSIX adapter 在 Linux/macOS shell 下的执行结果。

因此本报告只确认 validator、fixture、测试和 Windows adapter 的静态/本地结果，不把它们表述成完整运行时验收。
