# Understand-Anything: Update Knowledge Graph

Update/rebuild the project's Understand-Anything knowledge graph.

---

## Rebuild

Understand-Anything requires manual rebuild after code changes. To update the
graph, re-run:

```
/understand
```

This re-scans the entire project and regenerates:
- `knowledge-graph.json` — full graph data (replaced)
- `understand-graph.html` — interactive viewer (regenerated with new data)
- `intermediate/` — intermediate artifacts (updated)

---

## When to Rebuild

- After significant code changes (new files, refactors, restructures)
- After a `git pull` or branch switch
- When the dashboard shows outdated modules or missing dependencies
- After adding new source directories to the project

---

## Incremental vs Full Rebuild

Understand-Anything always does a **full rebuild** — it re-scans all files,
rebuilds the import graph, re-runs community detection, and regenerates all
outputs. This ensures consistency but can be slower on very large projects.

---

## Verify Update

After rebuilding:

1. Check `.understand-anything/knowledge-graph.json` modification time
2. Open `.understand-anything/understand-graph.html` in a browser to verify
   the visual dashboard reflects current code
3. Run a test query via `/understand-chat`

---

## Troubleshooting

If `/understand` fails:

1. Ensure the understand-anything skill is installed:
   - Check `.codebuddy/skills/understand/` or `~/.codebuddy/skills/understand/`
   - Re-run install script if missing
2. Check for sufficient disk space (intermediate files are generated)
3. Large projects may take several minutes — wait for completion

---

**Verdict**: COMPLETE — Understand-Anything knowledge graph updated.
