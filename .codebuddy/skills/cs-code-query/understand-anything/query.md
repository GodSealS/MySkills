# Understand-Anything: Query Existing Graph

Resolve target root and `.understand-anything/knowledge-graph.json`; use `.ua/` only
where the installed skill supports it. Check parseable data, queryability, and coverage
separately. Missing/unusable data leads to source search, not automatic `/understand`
execution or installation.

## Native Query Flow

Discover and read installed `understand-chat`. Its `/understand-chat` entry reads
Understand-Anything's own graph; it is not a generic adapter for CodeGraph or Graphify.
If supported, pass the explicit target project path with the question. Without that
skill, read existing JSON and select relevant nodes/edges; label the source correctly.

1. Inspect `project` metadata and actual node/edge schema. Supported graphs may include
   file, function, class, module, config, and document nodes; do not assume every graph
   is module-only or contains every supported node type.
2. Compare available baseline (`project.gitCommitHash`, analysis metadata, or manifests)
   with the target checkout. Validate recorded commits before using them in Git
   commands. Examine project-scoped committed differences, staged/unstaged changes,
   and untracked files, excluding generated graph artifacts. Equal HEAD does not
   cover uncommitted work; missing Git metadata means freshness is unknown, not that
   querying must stop.
3. Search names, summaries, tags, and paths, then relevant edges/layers. Extract bounded
   results instead of loading the entire graph into context.
4. Verify files and important dependencies/behavior against source. Supplement missing
   or stale results with source search. Use the main skill's candidate union and flow
   checks for SysDocs work.

Optional visual navigation uses the installed version's supported dashboard; do not
require or promise a particular generated HTML artifact. Report source, graph path,
coverage/freshness gaps, and scoped verdict. Matching graph/document summaries are not
independent proof of source or document correctness.
