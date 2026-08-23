# CodeGraph: Query Knowledge Graph

Query the project's CodeGraph knowledge graph to answer code-related questions.

---

## Prerequisites

- `.codegraph/` directory must exist in the project root
- CodeGraph must be registered to CodeSquad (MCP bridge auto-connects)

If `.codegraph/` does not exist, go back to Phase 3 of the main SKILL.md
or load `codegraph/create.md` to create it first.

---

## Query Flow

### 1. Use `/understand-chat` (CodeBuddy)

CodeGraph integrates with CodeSquad via MCP bridge, making its tools available
through the standard understand-chat flow. The most reliable approach is:

```
/understand-chat [user's question rephrased for graph query]
```

**Rephrasing examples**:

| User asks                              | Route as                                    |
|----------------------------------------|---------------------------------------------|
| "How does the chat system work?"       | `/understand-chat chat system architecture and flow` |
| "Where is session handling defined?"   | `/understand-chat session handling location and dependencies` |
| "What calls the agent runner?"         | `/understand-chat agent-runner callers and dependents` |
| "Find all API routes"                  | `/understand-chat API route definitions and structure` |

### 2. Interpret Results

After `/understand-chat` returns:

1. **Summarize** findings in plain language
2. **If answer is complete**: present it directly with file paths and line references
3. **If deeper investigation is needed**: use results as a map, then `Read` the specific files identified

### 3. CodeGraph-Specific Strengths

CodeGraph provides:
- **Semantic code graph**: relationships between functions, classes, modules
- **Call chains**: who calls what, dependency chains
- **Symbol resolution**: find definitions, references, implementations
- **20+ language support**: TypeScript, Python, C#, C++, GDScript, etc.
- **Auto-sync**: file watcher keeps the graph up-to-date (no manual refresh needed)

---

## Fallback

If `/understand-chat` returns no results:

1. Check that CodeGraph is running (MCP connection active)
2. Try re-initializing: load `codegraph/update.md`
3. If still failing, fall back to traditional search (Glob → Grep → Read)

---

**Verdict**: COMPLETE — query answered via CodeGraph knowledge graph.
