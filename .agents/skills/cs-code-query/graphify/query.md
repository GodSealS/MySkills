# Graphify: Query Existing Graph

Resolve actual project root and `graphify-out/graph.json` (or configured graph path).
Confirm parseable data, then separately check queryability and task coverage. Missing
data leads directly to source search, never implicit creation.

## Select an Available Interface

Discover Graphify's actual MCP tools/schemas or inspect installed `graphify --help`.
Do not assume MCP registration or route through `/understand-chat`. Supported CLI
versions provide:

```text
graphify query "<graph vocabulary terms>" --graph "<absolute-graph-json>" --budget 2000
graphify explain "<node label>" --graph "<absolute-graph-json>"
graphify path "<source label>" "<target label>" --graph "<absolute-graph-json>"
graphify affected "<node label>" --graph "<absolute-graph-json>"
```

Confirm the installed version supports selected commands/flags before invoking; an
adjacent source checkout or installed skill may differ from the executable. Graphify
query commands can write logs/stamps. For strict read-only reviews, read/parse existing
JSON and traverse relevant nodes/edges without writes, or use source fallback. Do not
run `save-result`, `reflect`, or refresh as a query prerequisite; saved answers can
feed unverified claims back into the graph.

## Query and Source Checks

1. Inspect relevant node labels to select matching vocabulary, including real labels
   for cross-language questions. Literal matching is not general semantic search;
   zero matches do not prove no impact. Do not invent node labels or edges.
2. Keep graph path explicit. Read node `source_file`/`source_location`, edge relation,
   direction, and confidence when present. Inferred edges are candidates, not facts.
3. Check extraction metadata/manifests, actual files, and task changes. Changed prose
   can be absent despite a successful code-only refresh.
4. Verify relevant source/configuration or canonical documents before stating claims.
   If data is stale, absent, or malformed, identify the gap and search source.
5. For SysDocs impact, union graph, document summary/business-term, and source candidates.
   Follow the main skill's disagreement and high-risk flow checks.

Report real interface, index path, checked scope, and omissions under the main verdict
contract. Neither queries nor graph refresh certify document correctness.
