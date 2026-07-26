# Understand-Anything: Create Knowledge Graph

Create an Understand-Anything knowledge graph for the current project.

---

## Step 1: Verify Understand-Anything is Installed

Understand-Anything is a CodeBuddy skill (not a standalone CLI). Check if the
skill exists:

```bash
# Check if the skill directory exists
ls .codebuddy/skills/understand/   # Unix
dir .codebuddy\skills\understand\  # Windows
```

Or check globally:
```bash
ls ~/.codebuddy/skills/understand/   # Unix
dir %USERPROFILE%\.codebuddy\skills\understand\  # Windows
```

---

## Step 2: Install if Missing

If not installed, run the install script:

```powershell
# Windows PowerShell
iwr -useb https://raw.githubusercontent.com/GodSealS/Understand-Anything/main/install.ps1 | iex
. .\install.ps1 codesquad
```

This installs the understand-anything skill and its dependencies
(`@understand-anything/core`, tree-sitter parsers).

---

## Step 3: Initialize Knowledge Graph for This Project

Run from the project root:

```
/understand
```

This will:
- Scan all source files with language-aware tree-sitter parsers
- Build an import graph with resolved module dependencies
- Run Louvain community detection to create natural module clusters (layers)
- Generate an interactive architecture dashboard (`understand-graph.html`)
- Create tours and identify god nodes

**Expected output**: `.understand-anything/` directory is created, containing:
- `knowledge-graph.json` — the full graph data
- `understand-graph.html` — interactive viewer (self-contained)
- `intermediate/` — intermediate build artifacts (scan results, batches, etc.)

---

## Step 4: Verify

After `/understand` completes:

1. Confirm `.understand-anything/` directory exists with `knowledge-graph.json`
2. Open `understand-graph.html` in a browser to explore the architecture visually
3. The graph is MODULE-level (not per-file), with layers, tours, and god nodes

---

## Step 5: Completion Message

After successful creation:

> Understand-Anything 知识图谱已创建完毕！`.understand-anything/` 目录已生成，包含交互式架构图。
>
> 可以直接打开 `understand-graph.html` 在浏览器中查看可视化架构，或直接向我提问代码相关问题。

**Verdict**: COMPLETE — Understand-Anything knowledge graph initialized and ready for queries.
