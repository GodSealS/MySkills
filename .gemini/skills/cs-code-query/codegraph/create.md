# CodeGraph: Create Knowledge Graph

Use only for explicit creation or already-authorized setup. Ordinary code questions
and backend selection alone never enter this operation.

1. Resolve the target project and check for an existing index. If present, use update
   only when refresh is requested; initialization is not a rebuild.
2. Discover the installed CLI and inspect `codegraph --help` and `codegraph init --help`.
   A tool source checkout is not an installed interface. If missing, report the
   prerequisite; install only within explicitly authorized setup scope using the
   tool's actual instructions. Do not silently register platforms, change global
   agent configuration, or download an executable.
3. For versions exposing `init [path]`, run:

   ```text
   codegraph init "<project-root>"
   ```

   Replace the placeholder with the verified root. Review actual output for skipped
   files, parse failures, and setup choices. Watcher activation and MCP registration
   depend on the installation; do not promise either from init alone.
4. Verify index artifacts and use `query.md` for a real query of a known symbol.
   Check indexed coverage against requested source scope and record omitted files
   and source version/worktree state.

Only report COMPLETE when creation and these checks succeed. If indexing succeeded
but query access or coverage verification failed, report PARTIAL with the actual gap.
Creating a knowledge graph does not create or verify SysDocs.
