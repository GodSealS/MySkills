# Understand-Anything: Create Knowledge Graph

Use only for explicit creation or already-authorized setup. Ordinary queries do not
require building a graph.

1. Discover installed `understand` via the current host's skill catalog or configured
   skill paths. Read actual instructions; do not assume this backend is exclusive to
   CodeBuddy or is a standalone CLI. If missing, report the prerequisite and install
   only within already-authorized setup scope.
2. Resolve target project and output directory. If an index exists, use update only
   when refresh is requested. Verify installed worktree redirect behavior so selected
   checkout and index provenance align; do not silently analyze another checkout.
3. Invoke installed `understand` (commonly `/understand` with target path) using its
   supported syntax/mode. Observe parse failures, unsupported files, intermediate
   results, and actual completion status.
4. Check parseable `knowledge-graph.json` at resolved data location, metadata, and
   requested coverage. Do not require a hardcoded HTML dashboard or module-only graph
   shape: outputs vary by version.
5. Follow `query.md` for a known symbol/path and verify relationships against source.
   Record baseline and working-tree limitations.

Report COMPLETE only when creation and scoped query/coverage checks succeed; otherwise
PARTIAL/FAILED. Creating a graph does not initialize or verify SysDocs.
