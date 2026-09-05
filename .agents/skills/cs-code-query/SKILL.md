---
name: cs-code-query
description: "Routes all code-related queries to the project knowledge graph. Supports three backends: CodeGraph (recommended), Understand-Anything, and Graphify. Provides create, query, and update operations for each. / 将所有代码相关查询路由到项目知识图谱，支持三种后端：CodeGraph（推荐）、Understand-Anything、Graphify，每种后端提供创建、查询、更新操作。"
---

# Code Query via Knowledge Graph

Route code questions through a knowledge graph — **CodeGraph** (recommended),
**Understand-Anything**, or **Graphify**. Each backend supports **create**,
**query**, and **update** via 9 on-demand sub-files:
`codegraph/`, `understand-anything/`, `graphify/` each with `{create,query,update}.md`.

---

## Phase 1: Recognize Intent

Any question about the codebase — how it works, where things live, what calls what.

---

## Phase 2: Detect Knowledge Base Status

Check which knowledge bases exist in the project by listing these directories:

| Knowledge Base       | Project Directory        | Tool CLI        |
|----------------------|--------------------------|-----------------|
| CodeGraph            | `.codegraph/`            | `codegraph`     |
| Understand-Anything  | `.understand-anything/`  | understand-anything (via CodeBuddy skill) |
| Graphify             | `graphify-out/`          | `graphify`      |

**Action**: Use `ListDir` to check existence of `.codegraph/`, `.understand-anything/`, and `graphify-out/` in the project root. Then use `Bash` to check which CLIs are available:

```bash
# Check CLI availability (Windows)
where codegraph 2>$null; where graphify 2>$null

# Check CLI availability (Unix)
which codegraph 2>/dev/null; which graphify 2>/dev/null
```

### Status Matrix

| Directory exists? | CLI available? | Status                                     |
|-------------------|----------------|--------------------------------------------|
| YES               | YES            | **READY** — can query immediately          |
| YES               | NO             | **STALE** — KB exists but CLI missing, can still query via MCP bridge |
| NO                | YES            | **UNINITIALIZED** — CLI installed, need to create KB |
| NO                | NO             | **MISSING** — nothing installed            |

---

## Phase 3: Bootstrap Missing KB

If NO knowledge base directory exists:

1. **Check CLI availability** first using the commands above.

2. **If at least one CLI is installed**: tell the user which one(s) are available, recommend codegraph, and offer to create the KB:

   > 检测到以下知识库工具已安装但尚未为项目创建知识图谱：
   > - CodeGraph ✓（推荐）
   > - [其他已安装的工具]
   >
   > 是否需要我为项目创建知识图谱？推荐使用 **CodeGraph**（最快、最省资源、100%本地运行）。
   > 回复 "codegraph" / "understand-anything" / "graphify" 或 "all"。

3. **If NO CLI is installed**: ask the user which to install (recommend CodeGraph). Point to the corresponding `create.md` for installation instructions:

   > 项目尚未配置任何知识图谱。推荐安装 **CodeGraph**（最快、最省资源、100%本地运行）。
   >
   > 安装命令详见 `<kb>/create.md`，或参考 README.md「本地知识库集成」章节。
   >
   > 请选择：codegraph / understand-anything / graphify

4. **After user selects a KB**, load and execute the corresponding `create.md`:
   - `Read <kb>/create.md`
   - Follow its instructions to install (if needed) and initialize the KB
   - **Completion criterion**: Verify the KB directory exists via `ListDir`, then remind: **知识图谱已就绪，可以开始查询了！**

---

## Phase 4: Route to Operation

Based on user intent AND available KBs, route to the appropriate sub-file.

### Detect Operation Type

| User says                           | Operation | Sub-file                    |
|-------------------------------------|-----------|-----------------------------|
| "查询/搜索/查找/理解/解释 X"        | **query** | `<kb>/query.md`             |
| "创建/构建/初始化/生成知识图谱"      | **create**| `<kb>/create.md`            |
| "更新/刷新/重建/同步知识图谱"        | **update**| `<kb>/update.md`            |
| General code question               | **query** | `<kb>/query.md` (default)   |

### Select Knowledge Base

An optional KB selector lets the user force a specific backend. All of these forms are
accepted and equivalent: `--kb CG`, `--kb codegraph`, `CG`, `codegraph`.

| Selector | Backend             |
|----------|---------------------|
| `CG`     | CodeGraph           |
| `US`     | Understand-Anything|
| `GR`     | Graphify            |

**If the selector IS provided**: resolve it to the backend and use it directly — skip
auto-matching. If the selected KB is MISSING/UNINITIALIZED (Phase 2), go to Phase 3 to
create it before querying.

**If the selector is OMITTED (no input)**: auto-match —
- **Prefer an existing KB**: if multiple exist, prefer codegraph > understand-anything > graphify
- **If none exist**: go back to Phase 3

### Load and Execute

Once KB and operation are determined, read the corresponding sub-file:

```
Read: <kb>/<operation>.md
```

Then follow its instructions exactly. Load only the sub-file needed for the current operation.

---

## Phase 5: Multi-KB Queries

If the user asks to query across multiple KBs (or "query all"):

1. Check which KBs exist (Phase 2)
2. For each existing KB, load its `query.md` sequentially
3. Present results from each KB, clearly labeled by source
4. Note discrepancies between KB results

---

## Phase 6: Verdict

After completing any operation, provide a verdict:

- **COMPLETE** — query/create/update finished successfully via knowledge graph
- **PARTIAL** — operation completed but some KBs were unavailable
- **FAILED** — operation could not complete (explain why, suggest fallback)

**Fallback**: If the knowledge graph returns no results or is unavailable and cannot be created:
- Inform the user clearly
- Fall back to traditional code search (Glob → Grep → Read) as secondary approach
- Suggest installing a knowledge graph tool
