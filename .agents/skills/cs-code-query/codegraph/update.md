# CodeGraph: Update Existing Index

Require an existing index and explicit refresh or already-authorized maintenance.
If no index exists, report the prerequisite and continue independent source work;
do not initialize one. Query failures alone do not authorize mutation.

## Select the Actual Refresh Interface

Discover the installed CLI/MCP and help/schema first. In supported CLI versions:

```text
codegraph sync "<project-root>"
```

performs incremental synchronization. Use `codegraph index "<project-root>"` only
when the task calls for a full rebuild or incremental refresh cannot repair the
relevant index. Confirm replacement scope first. `codegraph init` can return
immediately for an existing index and is not a refresh substitute.

A watcher may already handle changes. Check indexed evidence before deciding refresh
is needed; watcher capability and directory mtime do not prove freshness. Do not
install or reconfigure the tool as an implicit repair.

## Verification

Record target root, operation, indexed scope, and failures/skips. Follow `query.md`
to query a changed/new symbol, confirm renamed/deleted items no longer mislead, and
compare affected relationships with source. Include staged, unstaged, and untracked
task changes rather than treating HEAD as the entire snapshot.

Report COMPLETE/PARTIAL/FAILED according to these results. Unknown coverage stays
unknown. Index refresh is not document validation; SysDocs checks remain with the
owning development/document workflow.
