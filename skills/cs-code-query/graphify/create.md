# Graphify: Create Knowledge Graph

Use only for explicit creation or already-authorized setup. Resolve target root, source
corpus, and output path first; an existing graph follows update when refresh is requested.
Do not create graphs as a condition of answering questions.

1. Discover installed CLI/skill/MCP interfaces and read the selected version's help or
   skill. If unavailable, report the prerequisite; install only when already authorized,
   using actual instructions. Do not assume bare `graphify` builds a graph: it may
   enter installation/help instead.
2. Choose extraction matching the authorized corpus. Versions exposing CLI extraction
   support `graphify extract "<project-root>" --code-only` for local code extraction.
   Mixed code/document extraction uses the installed Graphify skill or supported
   `extract` options with its configured provider. Do not claim code-only indexing
   covers prose, ADRs, images, or papers. Keep external provider use within authorized
   data scope; do not silently configure accounts/services.
3. Confirm output placement from installed help (for example, `--out` may denote a
   parent directory under which `graphify-out/` is written). Do not infer paths from
   another version. Read errors and partial-extraction reports.
4. Check parseable data, then use `query.md` to query a known node at the explicit
   graph path. Verify source locations and requested code/document coverage, recording
   omissions and snapshot limitations.

Report COMPLETE only after creation, query, and scoped coverage checks succeed;
otherwise PARTIAL/FAILED. Do not promise integration with another backend's chat skill.
Graph creation does not generate or verify SysDocs.
