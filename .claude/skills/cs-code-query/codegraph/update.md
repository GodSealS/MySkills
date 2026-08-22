# CodeGraph: Update Knowledge Graph

Update/sync the project's CodeGraph knowledge graph.

---

## Auto-Sync (Default)

CodeGraph runs a file watcher after `codegraph init`. It automatically detects
file changes via OS native events and re-indexes affected files. **No manual
action is needed under normal usage.**

---

## Manual Rebuild

If the graph is stale, corrupted, or you want to force a full re-index:

```bash
# From project root
codegraph init
```

This re-scans the entire project and rebuilds the graph. The existing `.codegraph/`
data will be updated in-place.

---

## When to Rebuild

- After a `git pull` or branch switch that changed many files
- After a major refactor (file renames, directory restructuring)
- If queries return outdated or incorrect results
- After adding/removing large numbers of files

---

## Verify Update

After rebuilding:

1. Run a test query via `/understand-chat` to confirm results are current
2. Check `.codegraph/` modification time is recent

---

## Troubleshooting

If `codegraph init` fails:

1. Ensure `codegraph` CLI is installed: `codegraph --version`
2. Ensure you're in the project root directory
3. Check disk space (CodeGraph uses SQLite, typically < 100MB)
4. Try re-installing: `npm install -g @colbymchenry/codegraph`

---

**Verdict**: COMPLETE — CodeGraph knowledge graph updated.
