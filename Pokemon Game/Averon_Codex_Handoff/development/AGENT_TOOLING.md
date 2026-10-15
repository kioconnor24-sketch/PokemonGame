# Agent tooling: status, setup and verification

Written 2026-10-15 by Claude. Companion to [AGENT_ROLES.md](AGENT_ROLES.md) (who owns what) and [WORKFLOW.md](WORKFLOW.md) (PR/CI rules). GitHub issues, PRs and CI remain the authoritative coordination layer. Nothing here replaces them.

Status words: **installed** (software present), **configured** (project files exist), **connected** (live service reachable), **tested** (exercised and observed), **unavailable** (cannot be done in that environment).

## Status

| Item | Status | Evidence / limit |
| --- | --- | --- |
| GitHub coordination (claims, PRs, CI read) | connected, tested by Claude | CLAIM posted in issue #15; PR and check-run data read via REST |
| `CLAUDE.md` (`@AGENTS.md` import + Claude notes) | configured | Claude Code docs: a `CLAUDE.md` that imports `AGENTS.md` is read with it. Not yet observed in a fresh session |
| Project skills (4) in `.claude/skills/` | configured | Claude Code loads `.claude/skills/` per its docs. Not yet observed. **Codex discovery path unverified**: its docs page redirected to an unverified domain and was not followed |
| Graphify (local, `graphifyy`) | not installed | Cloud sandbox has no PyPI/npm access. Needs the owner's machine (below). Provenance verified |
| Graphify hosted (`api.graphify.com/mcp`) | not evaluated | Needs OAuth sign-in. Pricing not stated on the pages read. ChatGPT is not listed as a supported integration. Not recommended now |
| Ponytail | not installed | Source cloned and read, not run. Deferred (see below) |
| OmniRoute | deferred | Per owner instruction |
| ARM toolchain / mGBA in cloud sandbox | unavailable | apt and PyPI unreachable. CI is the build and native-test run |
| ChatGPT access to graphs/skills | untested | Use GitHub as the handoff layer |

## Provenance notes
- **Graphify:** the official PyPI package is **`graphifyy`** (double y), v0.9.91 (2026-10-14) at review time, Apache-2.0, published by GitHub Actions Trusted Publishing from `Graphify-Labs/graphify`. Do not use `graphiffy.com`, `graphifyyy`, or forks such as `sharkkyyy10/graphify-`. `Graphify-Labs/graphify-mcp` did not resolve; the MCP server is the optional `graphifyy[mcp]` extra.
- **Graphify behavior to review before enabling:** it can write project skill/instruction files, install Claude Code and git hooks (`graphify hook install` rebuilds on commit/checkout), log queries to `~/.cache/graphify-queries.log` (disable with `GRAPHIFY_QUERY_LOG_DISABLE=1`), and send non-code files (docs/PDFs/images) to a model backend. Code parsing is local (tree-sitter).
- **Ponytail:** MIT. Hooks run Node on session start, subagent start and every prompt; they read/write under `~/.claude` and spawn subprocesses; no network calls found. It shapes agent output, which conflicts with this project's rule that correctness outranks token savings. Benchmarks are the author's own.
- **Bundled runner:** `engine/tools/mgba/mgba-rom-test` is a prebuilt Linux ELF from upstream pokeemerald-expansion; its README lists the mGBA source commits. Hash recorded: `4304688a0b44007cca23c9e887af17c44530fd602ee3d1e57a232da397bec769`. Not rebuilt from source here.

## Recommended minimal setup
1. **Skills + `CLAUDE.md`** (this PR). One canonical copy in `.claude/skills/`; no per-agent duplicates until Codex discovery is verified, then add a sync check rather than hand-maintained copies.
2. **Graphify local, only if the owner wants it**, on the owner's machine (WSL, where the toolchain already lives):
   ```bash
   uv tool install graphifyy     # or: pipx install graphifyy
   graphify --help               # confirm commands and flags before running any of them
   graphify install              # registers the skill for the detected assistant
   ```
   Do not run `graphify hook install` until reviewed. Exclude `build/`, `*.gba`, `*.o`, `engine/tools/mgba/` and `evidence/` from indexing (exact exclusion mechanism to confirm in docs.graphify.com). Record index time, graph size and whether a query helped before adopting it.
3. **Ponytail:** defer. If tried, `lite` mode only, one branch, same task with and without it, judged on build and test results, not tokens.

## New-session setup (any agent)
1. Fetch `main`, open PRs, issue #15 comments, and newest `HANDOFF`.
2. Read root `AGENTS.md`, `AGENT_ROLES.md`, `WORKFLOW.md`, `TASKS.md`.
3. Claude Code: skills under `.claude/skills/` load automatically; check with `/context` that `CLAUDE.md` is listed.
4. Claim in issue #15 before touching shared files. Branch `claude/*` or `codex/*`.
5. After a merge, nothing to "refresh" for skills (they are files). If Graphify is adopted, rebuild the graph from the merged commit; the graph is a navigation aid, never the source of truth.

## Verification report (this PR)
| Check | Result |
| --- | --- |
| Claude can retrieve project knowledge | PASS (GitHub + repo files). Codex: UNTESTED |
| Skills discoverable | UNTESTED (frontmatter validated locally only) |
| Shared instructions consistent | PARTIAL: the owner's setup brief calls Claude "technical lead" and counts three agents; merged `AGENT_ROLES.md` has four agents with Claude and Codex as peers. Merged file kept; owner to confirm |
| A finding recorded by one agent and located by another | UNTESTED (only one agent has acted) |
| Sample handoff without conflicting edits | UNTESTED |
| ChatGPT can read the handoff info | UNTESTED |
| No paid service enabled | PASS |

## Owner actions
- Decide whether the role wording in the setup brief or the merged `AGENT_ROLES.md` governs.
- If Graphify is wanted: run step 2 above in WSL and report the output of `graphify --help`.
- A person with Codex access should confirm where Codex discovers repository skills.
