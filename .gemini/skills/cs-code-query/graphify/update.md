# Graphify: Update Existing Graph

Require an existing graph and explicit refresh or already-authorized maintenance.
Resolve actual graph and scan root; missing data does not authorize creation. Read
installed interface help/skill before choosing a refresh method.

## Match Refresh to Coverage

- In supported versions, `graphify update "<project-root>"` re-extracts **code**.
  It does not certify freshness of document, paper, or image-derived relationships.
- Mixed corpus refresh uses the installed skill's supported update flow (such as
  `/graphify --update`) or CLI extraction with the configured provider supported by
  that version. Some versions support manifest-based incremental extraction; do not
  describe every refresh as a full rebuild.
- Use force/full rebuild only when required by the requested repair and supported
  by the actual interface. Check replacement scope and preserve unrelated data;
  do not delete output directories as a troubleshooting shortcut.
- If the interface/provider for affected prose is unavailable, refresh authorized
  supported scope if useful and report the gap. Do not present code-only success
  as full mixed-corpus completion or silently reinstall.

## Verification

Inspect output for skipped/failed extraction and confirm graph path. Use `query.md`
to query changed/new nodes, check renamed/removed items, and compare locations and
important relationships with source or canonical prose. Verify scope against available
manifests/provenance and working-tree changes. Recent mtime and exit success alone
are insufficient; unknown coverage stays unknown. An unchanged graph may mean no
changes or a refused rebuild; check output.

Report actual refreshed/unverified scope with COMPLETE/PARTIAL/FAILED. Refresh does
not verify SysDocs; the owning workflow performs content checks separately.
