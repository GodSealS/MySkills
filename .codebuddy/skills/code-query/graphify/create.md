# Graphify: Create Knowledge Graph

Create a Graphify knowledge graph for the current project.

---

## Step 1: Verify Graphify CLI is Installed

```bash
where graphify   # Windows
which graphify   # Unix
```

If not installed, install via one of:

```bash
# Using uv (recommended)
uv tool install "graphifyy @ git+https://github.com/safishamsi/graphify@v8"

# Using pipx
pipx install "graphifyy @ git+https://github.com/safishamsi/graphify@v8"
```

> Prerequisites: Python 3.10+, `uv` or `pipx`

---

## Step 2: Initialize Knowledge Graph for This Project

Run from the project root:

```bash
graphify
```

This will:
- Scan all source files in the project
- Build a knowledge graph with entity extraction, relationships, and topic clustering
- Generate god nodes (key architectural components)
- Run community detection for module grouping

**Expected output**: `graphify-out/` directory is created in the project root,
containing the graph data files.

---

## Step 3: Verify

After `graphify` completes:

1. Confirm `graphify-out/` directory exists
2. The graph can be queried via `/understand-chat` once integrated

---

## Step 4: Completion Message

After successful creation:

> Graphify 知识图谱已创建完毕！`graphify-out/` 目录已生成。
>
> 现在可以直接向我提问任何代码相关问题，我会通过知识图谱查询项目架构和代码关系。

**Verdict**: COMPLETE — Graphify knowledge graph initialized and ready for queries.
