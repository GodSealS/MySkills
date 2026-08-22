# Graphify: Update Knowledge Graph

Update/rebuild the project's Graphify knowledge graph.

---

## Rebuild

Graphify requires manual rebuild after code changes. To update the graph,
re-run from the project root:

```bash
graphify
```

This re-scans the entire project and regenerates all graph data in `graphify-out/`.

---

## When to Rebuild

- After significant code changes (new files, refactors, restructures)
- After a `git pull` or branch switch
- When queries return outdated information
- After adding/removing modules or directories

---

## Incremental vs Full Rebuild

Graphify always performs a **full rebuild** — re-scanning all files, re-running
entity extraction, relationship detection, community detection, and god node
identification. The `graphify-out/` directory is replaced with fresh output.

---

## Verify Update

After rebuilding:

1. Confirm `graphify-out/` modification time is recent
2. Run a test query via `/understand-chat` to verify current results

---

## Troubleshooting

If `graphify` fails:

1. Ensure graphify is installed: `graphify --version`
2. Ensure Python 3.10+ is available: `python --version`
3. Reinstall if needed:
   ```bash
   uv tool install "graphifyy @ git+https://github.com/safishamsi/graphify@v8"
   ```
4. Check internet connectivity (git+https install requires network)

---

**Verdict**: COMPLETE — Graphify knowledge graph updated.
