# Graphify: Query Knowledge Graph

Query the project's Graphify knowledge graph to answer code-related questions.

---

## Prerequisites

- `graphify-out/` directory must exist in the project root

If `graphify-out/` does not exist, go back to Phase 3 of the main SKILL.md
or load `graphify/create.md` to create it first.

---

## Query Flow

### 1. Use `/understand-chat` (CodeBuddy)

```
/understand-chat [user's question rephrased for graph query]
```

**Rephrasing examples**:

| User asks                              | Route as                                    |
|----------------------------------------|---------------------------------------------|
| "How does the chat system work?"       | `/understand-chat chat system architecture and flow` |
| "Where is authentication handled?"     | `/understand-chat authentication components and flow` |
| "What modules exist?"                  | `/understand-chat project module structure and god nodes` |
| "Show dependencies of the CLI"         | `/understand-chat CLI module dependencies and relationships` |

### 2. Interpret Results

After `/understand-chat` returns:

1. **Summarize** findings, highlighting god nodes and key relationships
2. **If answer is complete**: present it directly
3. **If deeper investigation is needed**: use graph results as a map to read
   specific files via `Read` or `Grep`

### 3. Graphify-Specific Strengths

Graphify provides:
- **God nodes**: identifies the most architecturally significant components
- **Community detection**: natural module groupings via Louvain algorithm
- **Entity extraction**: functions, classes, modules as graph entities
- **Topic clustering**: groups related code by topic/domain
- **Path finding**: trace relationships between any two entities

---

## Fallback

If `/understand-chat` returns no results:

1. Check that `graphify-out/` exists and contains graph data
2. Try rebuilding: load `graphify/update.md`
3. If still failing, fall back to traditional search (Glob → Grep → Read)

---

**Verdict**: COMPLETE — query answered via Graphify knowledge graph.
