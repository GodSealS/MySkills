# CodeGraph: Query Existing Index

Apply the main skill's separate existence, queryability, and coverage checks. Resolve
the target project and its `.codegraph/` index; if absent or unusable, report the
condition and search source directly. Do not initialize or refresh during a query.

## Interface Discovery

Discover the host's actual CodeGraph MCP tools and input schemas. A known interface
is `codegraph_explore` with `query` and `projectPath`; narrower tools such as
`codegraph_search`, `codegraph_node`, and `codegraph_impact` may not be exposed.
Only invoke tools actually available; pass the verified target project path.

If MCP is unavailable, discover the CLI and inspect `codegraph --help` and relevant
subcommand help. Supported versions provide these examples:

```text
codegraph status "<project-root>" --json
codegraph query "<symbol>" --path "<project-root>" --json
codegraph explore "<question or symbols>" --path "<project-root>"
codegraph callers "<symbol>" --path "<project-root>" --json
codegraph impact "<symbol>" --path "<project-root>" --json
```

Replace placeholders with safely quoted arguments; confirm flags against the installed
version. Do not invent an MCP-to-skill bridge or use `/understand-chat`. For strict
read-only constraints, inspect backend database/watcher side effects first and use
source fallback when the available interface cannot honor those constraints.

## Query and Verification

1. Probe a known symbol/path and verify the reported project/index location.
2. Query the needed symbols, call paths, or impact candidates. Inspect status metadata
   and omissions; a running watcher does not guarantee coverage or freshness.
3. Cross-check relevant current source, including renamed/new files and uncommitted
   work missing from the index. A returned source excerpt still needs its location
   and snapshot checked. Empty results trigger source search, not automatic rebuild.
4. For document work, union graph candidates with SysDocs summary/business-term and
   source candidates under the main skill. Report discrepancies and provenance.

Follow the main verdict contract: identify CodeGraph vs source fallback and unknown
coverage. Query completion does not certify SysDocs contents.
