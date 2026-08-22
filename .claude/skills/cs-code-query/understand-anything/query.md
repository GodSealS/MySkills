# Understand-Anything: Query Knowledge Graph

Query the project's Understand-Anything knowledge graph to answer code-related questions.

---

## Prerequisites

- `.understand-anything/` directory must exist with `knowledge-graph.json`
- The graph is **module-level** (not per-file), so answers focus on architecture,
  component relationships, and module structure

If `.understand-anything/` does not exist, go back to Phase 3 of the main
SKILL.md or load `understand-anything/create.md` to create it first.

---

## Query Flow

### 1. Use `/understand-chat` (CodeBuddy)

```
/understand-chat [user's question rephrased for architecture-level query]
```

**Rephrasing — think MODULE-LEVEL, not file-level**:

| User asks                              | Route as                                         |
|----------------------------------------|--------------------------------------------------|
| "How is the project organized?"        | `/understand-chat project module structure and layers` |
| "What depends on the chat module?"     | `/understand-chat chat module dependencies and consumers` |
| "Show me the architecture"             | `/understand-chat project architecture layers and god nodes` |
| "What's the most complex module?"      | `/understand-chat module complexity metrics and critical components` |

### 2. Interpret Results

After `/understand-chat` returns:

1. **Summarize** module-level findings (layers, dependencies, god nodes)
2. **If user needs file-level detail**: use the module info as a map, then
   `Read` or `Grep` within the identified module directory
3. **If visual exploration is better**: direct the user to open
   `.understand-anything/understand-graph.html` in a browser

### 3. Understand-Anything-Specific Strengths

- **Module-level architecture**: layers, community detection, god nodes
- **Interactive dashboard**: `understand-graph.html` for visual exploration
- **Import graph**: real resolved import edges between modules (not just directories)
- **Tours**: guided walks through related components
- **Complexity metrics**: per-module complexity and stability scores

---

## Dashboard Access

For visual exploration, the dashboard is self-contained:

- File: `.understand-anything/understand-graph.html`
- Opens in any browser, no server needed
- Shows: layers (color-coded columns), nodes, edges, tours, search
- Data is embedded in `<script id="graph-data">` tag

---

## Fallback

If `/understand-chat` returns no results:

1. Check that `knowledge-graph.json` exists and is not empty
2. Try rebuilding: load `understand-anything/update.md`
3. If still failing, fall back to traditional search (Glob → Grep → Read)

---

**Verdict**: COMPLETE — query answered via Understand-Anything knowledge graph.
