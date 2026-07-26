# CodeGraph: Create Knowledge Graph

Create a CodeGraph knowledge graph for the current project.

---

## Step 1: Verify CodeGraph CLI is Installed

```bash
where codegraph   # Windows
which codegraph   # Unix
```

If not installed, install via one of:

```powershell
# Windows (recommended)
irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex
```

```bash
# npm (cross-platform)
npm install -g @colbymchenry/codegraph
```

```bash
# npx (no install)
npx @colbymchenry/codegraph
```

> Note: CodeGraph fork optimized for CodeSquad/CodeBuddy:
> https://github.com/GodSealS/codegraph/tree/codebuudy

---

## Step 2: Register CodeGraph to CodeSquad Platform

```bash
# Interactive install (auto-detects CodeSquad and configures MCP)
codegraph install

# Non-interactive, register to CodeSquad only
codegraph install --target=codesquad --yes

# Project-local config (does not modify global settings)
codegraph install --target=codesquad --location=local
```

---

## Step 3: Initialize Knowledge Graph for This Project

Run from the project root:

```bash
codegraph init
```

This will:
- Scan all source files in the project
- Build a semantic code knowledge graph (SQLite, local)
- Start a file watcher that auto-syncs changes via OS native events

**Expected output**: `.codegraph/` directory is created in the project root.

---

## Step 4: Verify

After `codegraph init` completes:

1. Confirm `.codegraph/` directory exists
2. CodeSquad CLI auto-discovers and connects CodeGraph via MCP bridge

---

## Step 5: Completion Message

After successful creation:

> CodeGraph 知识图谱已创建完毕！`.codegraph/` 目录已生成，文件监听器正在自动同步代码变更。
>
> 现在可以直接向我提问任何代码相关问题，我会通过知识图谱查询项目架构和代码关系。

**Verdict**: COMPLETE — CodeGraph knowledge graph initialized and ready for queries.
