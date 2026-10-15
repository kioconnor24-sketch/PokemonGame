# Preserved Codex tooling trial — not a merge candidate

Issue #24 directs reconciliation with PR #19 rather than another skill set.
Codex relinquishes its duplicate six skills and entry-point implementation in
favor of PR #19's canonical skills and PR #18's Claude entry point. This branch
preserves the earlier work; it has no PR and must not be merged wholesale.
Roles remain the owner's approved four-agent peer co-lead arrangement.

## Unique work preserved for optional later review

- `scripts/configure-local-graphify.py`: merges local stdio MCP configuration,
  preserves unrelated servers, rejects conflicting settings, limits Codex tools
  to five graph reads. Three isolated host tests passed. Not run against either
  real client's configuration; actual client connections remain UNTESTED.
- `scripts/refresh-agent-knowledge.ps1`: code-only index refresh with commit,
  dirty-state and graph hash provenance. Wrapper/incremental refresh UNTESTED.
- `scripts/setup-agent-skills.ps1`: canonical-directory adapter, executed twice
  successfully on Windows. Do not run it over PR #19's committed Claude shims;
  it deliberately refuses a different existing directory. Client discovery
  remains UNTESTED. PR #19 shims are the preferred shared approach.
- `.graphifyignore`: local code-navigation exclusions, including assets,
  binaries, caches, tools and client configuration. No lifecycle hooks enabled.

## Actual local observations from the earlier authorized trial

Graphify `graphifyy[mcp]==0.9.91` is installed in an ignored, isolated Windows
venv; `pip check` passed. Reviewed upstream source was
`10130e79ed9caf8f60d998073e097531eaa1a395`.
Initial code-only extraction on dirty `codex/shared-agent-tooling`, based on
main `36cb7ca9039f4203642a44d7bf147a15ac515a3f`, produced 25,650 nodes and
97,296 edges in about 168 seconds. There were 77 parse-warning files and 1,485
files without extracted symbols. Documents were not semantically indexed.
Known-symbol CLI queries for `DoWhiteOut` and its direct `WarpIntoMap` call
matched source. This does not prove complete C/macro/script coverage, MCP client
integration, refresh performance or QUEST runtime acceptance. The graph is now
stale and must not be treated as current source evidence.

Ponytail v5.2.0 source `84740e3d344b69b4a133201fa519eb37a62a2b2a` was inspected.
Its isolated upstream hook test failed on Windows/Node 24.19.0:
`statusline nudge must reference the CLAUDE_CONFIG_DIR settings.json`.
Hooks remain disabled. No measured token or correctness benefit is established.
No hosted Graphify connection, OAuth, paid service or OmniRoute was enabled.

PR #19 `ee53feeda999897b0d2f517d25c715d7baffa8f9` was independently checked:
14 changed files decode as UTF-8, all 6 canonical skills pass the standard
validator, and all 6 Claude shim paths resolve to their canonical skill.
No GBA build is required for this preserved tooling-only snapshot. No engine,
maps, flags, saves, workflows or gameplay generators were changed.
