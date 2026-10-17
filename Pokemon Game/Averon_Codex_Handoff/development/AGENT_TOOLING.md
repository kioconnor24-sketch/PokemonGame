# Agent tooling: status, setup and verification

Written 2026-10-15 by Claude, corrected 2026-10-16 after review. Companion to [AGENT_ROLES.md](AGENT_ROLES.md) (who owns what) and [WORKFLOW.md](WORKFLOW.md) (PR/CI rules). GitHub issues, PRs and CI remain the authoritative coordination layer. Nothing here replaces them.

Status words: **installed** (software present), **configured** (project files exist), **connected** (live service reachable), **tested** (exercised and observed), **unavailable** (cannot be done in that environment).

## Status

| Item | Status | Evidence / limit |
| --- | --- | --- |
| GitHub coordination (claims, PRs, CI read) | connected, tested by Claude | CLAIM posted in issue #15; PR and check-run data read via REST |
| `CLAUDE.md` (`@AGENTS.md` import + Claude notes) | configured | Claude Code docs: a `CLAUDE.md` that imports `AGENTS.md` is read with it. Not yet observed in a fresh session |
| Project skills | merged (PR #19) | Per the Issue #22 decision, PR #19 is the shared canonical skill set. This PR adds no skills |
| Graphify local (`graphifyy`, optional `graphifyy[mcp]` extra) | opt-in; not installed by Claude | Not installed in Claude's environments. Codex reports an earlier authorized, isolated `graphifyy` 0.9.91 install with code-only extraction and CLI queries in its own Windows environment (#18 comment 6202562911); its MCP connection is unverified |
| Graphify hosted MCP service (`https://api.graphify.com/mcp`) | opt-in; not configured, not authenticated | A separate hosted service, documented at [`Graphify-Labs/graphify-mcp`](https://github.com/Graphify-Labs/graphify-mcp) (checked 2026-10-16): Streamable HTTP, browser OAuth, account and plan apply separately. Not the same as local `graphifyy[mcp]`. Not recommended now |
| Ponytail | not installed | Source cloned and read, not run. Deferred (see below) |
| OmniRoute | deferred | Per owner instruction |
| ARM toolchain / mGBA in the initial cloud sandbox (report written 2026-10-15) | historical observation: unavailable | apt and PyPI were unreachable in that session; CI supplied its build/native evidence. Later Claude cloud sessions (2026-10-16) reported ARM GCC 13.2 preinstalled. Verify compiler, runner and network availability in the current runtime |
| Claude local WSL clone (observed on the owner's host) | tested | `/root/claude-dev/PokemonGame` on 2026-10-15: clean build of `main` `36cb7ca9` OK; `TESTS=Averon` 44/44 and `test/save.c` 4/4 pass; push verified via a deleted temporary branch; mGBA 0.10.5 boot smoke only (see Issue #15) |
| ChatGPT access to graphs/skills | untested | Use GitHub as the handoff layer |

## Provenance notes
- **Graphify:** the official PyPI package is **`graphifyy`** (double y), v0.9.91 (2026-10-14) at review time, Apache-2.0, published by GitHub Actions Trusted Publishing from `Graphify-Labs/graphify`. Do not use `graphiffy.com`, `graphifyyy`, or forks such as `sharkkyyy10/graphify-`. There are two distinct MCP options: the local server from the optional `graphifyy[mcp]` extra, and the hosted service documented at `Graphify-Labs/graphify-mcp`, whose server code is private and which needs a Graphify account and OAuth. Neither is installed or authenticated for this project.
- **Graphify behavior to review before enabling:** it can write project skill/instruction files, install Claude Code and git hooks (`graphify hook install` rebuilds on commit/checkout), log queries to `~/.cache/graphify-queries.log` (disable with `GRAPHIFY_QUERY_LOG_DISABLE=1`), and send non-code files (docs/PDFs/images) to a model backend. Code parsing is local (tree-sitter).
- **Ponytail:** MIT. Hooks run Node on session start, subagent start and every prompt; they read/write under `~/.claude` and spawn subprocesses; no network calls found. It shapes agent output, which conflicts with this project's rule that correctness outranks token savings. Benchmarks are the author's own.
- **Bundled runner:** `engine/tools/mgba/mgba-rom-test` is a prebuilt Linux ELF from upstream pokeemerald-expansion; its README lists the mGBA source commits. Hash recorded: `4304688a0b44007cca23c9e887af17c44530fd602ee3d1e57a232da397bec769`. Not rebuilt from source here.

## Recommended minimal setup
1. **`CLAUDE.md`** (this PR) and **shared skills** (PR #19, one canonical set). Add a sync check instead of hand-maintained per-agent copies.
2. **Graphify local, only if the owner wants it**, on the owner's machine (WSL, where the toolchain already lives):
   ```bash
   uv tool install graphifyy     # or: pipx install graphifyy
   graphify --help               # confirm commands and flags before running any of them
   graphify install              # registers the skill for the detected assistant
   ```
   Do not run `graphify hook install` until reviewed. Exclude `build/`, `*.gba`, `*.o`, `engine/tools/mgba/` and `evidence/` from indexing (exact exclusion mechanism to confirm in docs.graphify.com). Record index time, graph size and whether a query helped before adopting it.
3. **Ponytail:** defer. If tried, `lite` mode only, one branch, same task with and without it, judged on build and test results, not tokens.

## New-session setup (any agent)
1. Read the agent board (issue #31), then fetch `main`, open PRs, issue #15 comments, and the newest `HANDOFF`.
2. Read root `AGENTS.md`, `AGENT_ROLES.md`, `WORKFLOW.md`, `TASKS.md`.
3. Claude Code: check with `/context` that `CLAUDE.md` is listed. Shared skills come from merged PR #19.
4. Claim in issue #15 before touching shared files. Branch `claude/*` or `codex/*`.
5. After a merge, nothing to "refresh" for skills (they are files). If Graphify is adopted, rebuild the graph from the merged commit; the graph is a navigation aid, never the source of truth.

## Verification report (this PR)
| Check | Result |
| --- | --- |
| Claude can retrieve project knowledge | PASS (GitHub + repo files). Codex: UNTESTED |
| Skills discoverable | Merged in PR #19; not part of this PR |
| Shared instructions consistent | PASS: the owner keeps the current co-lead, four-role policy in `AGENT_ROLES.md` (#18 comment 6202562911) |
| A finding recorded by one agent and located by another | UNTESTED (only one agent has acted) |
| Sample handoff without conflicting edits | UNTESTED |
| ChatGPT can read the handoff info | UNTESTED |
| No paid service enabled | PASS |

## Owner actions
- If Graphify is wanted: run step 2 above in WSL and report the output of `graphify --help`.
- A person with Codex access should confirm where Codex discovers repository skills.
