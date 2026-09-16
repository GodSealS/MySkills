# Understand-Anything: Update Existing Graph

Require an existing graph plus explicit refresh or already-authorized maintenance.
If absent, report the prerequisite; do not turn update into creation. A failed query
is not authorization to rebuild.

1. Discover and read installed `understand`. Its workflow can choose incremental or
   full analysis based on graph/metadata and changes; do not assert it always rebuilds
   everything or invent an update command.
2. Resolve source root, existing data directory, and supported invocation (commonly
   `/understand` with target path). Verify worktree redirection before execution:
   analyzing the main checkout does not refresh a different worktree.
3. Run authorized update mode and inspect output. If incremental refresh cannot cover
   relevant scope, use supported full analysis only within authorized maintenance;
   do not reinstall or erase data as an implicit repair.
4. Read updated metadata/structure, then use `query.md` for a changed/new node and
   verify renamed/deleted nodes plus relationships against source. Account for
   project-scoped staged, unstaged, and untracked changes. A newer JSON timestamp,
   dashboard rendering, or equal HEAD is insufficient freshness evidence.

Report actual refreshed scope, missing coverage, and COMPLETE/PARTIAL/FAILED. Graph
update never substitutes for SysDocs content verification.
