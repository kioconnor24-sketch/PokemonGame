# Averon agent-tooling setup — reproducible, opt-in

Status: **Repository documentation and Agent Skills configuration only.** This file never proves a local package was installed, an MCP OAuth connection authenticated, an index populated, or a cloud plugin connected. See [AGENT_ROLES.md](AGENT_ROLES.md) and [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) for live ownership.

## Architecture and ownership

- **Codex and Claude** are **peer co-lead developers** with nonoverlapping claimed work. Codex coordinates shared engine/save integration by default; Claude has full authority to implement independent gameplay work.
- **ChatGPT QA** handles independently observed graphical mGBA playtesting when actually accessible; **ChatGPT review** handles architecture, coordination and bounded documentation.
- **GitHub issue #15, open PRs and HANDOFF comments** are the coordination and decision ledger. Comments do not awaken another running agent.
- **Graphify local** is an optional derived code-navigation index, **not** a multi-agent message bus or a substitute for GitHub. A local index on one machine is **not automatically shared** to another runtime. Treat index freshness and the checkout commit as prerequisites to relying on results.
- **Graphify Cloud** is a separate hosted MCP service with its own OAuth, repository indexing, plan/privacy model, and client compatibility. It is not the same as local `graphify-out/graph.json`.

## Six reusable skills

Canonical project skills are in repository root `.agents/skills/averon-*/SKILL.md`:
`averon-repository-orientation`, `averon-map-validation`, `averon-build-verification`, `averon-event-validation`, `averon-playtest-handoff`, `averon-bug-reporting`.

Claude-compatible `.claude/skills/averon-*/SKILL.md` files are lightweight pointers to these canonical definitions. Some clients may load project skills from either location; **verify skill discovery in each actual client**. Pointer-based wrappers may require the agent to read the referenced file; they are not proof that a client automatically follows it. Do not duplicate or change shared policy in these pointers.

## Graphify local — opt-in install by the developer who controls the computer

Project: https://github.com/Graphify-Labs/graphify ; current official docs: https://docs.graphify.com

1. Review package source, release provenance and installation hooks. Install Python 3.10+ and `uv` (or `pipx`) if missing.
2. In the developer's own terminal, if authorized, run `uv tool install graphifyy` (alternative: `pipx install graphifyy`).
3. Run `graphify install` **only after inspecting the files and hooks it will register for the active client**. Avoid rewriting existing user-level or repo-level agent configuration.
4. From the intended source checkout run `graphify .`. Its output may include `graphify-out/graph.json`, `graph.html`, and `GRAPH_REPORT.md`; avoid indexing build outputs, copyrighted binaries, saves and large ephemeral artifacts.
5. Check index metadata/version, git SHA and a known symbol with `graphify explain "<actual source symbol>"` and `graphify query "<actual question>"`. Run a second known-callers/path check and compare against code. Verify incremental refresh behavior before promising it.
6. Ignore local artifacts (`graphify-out/`, `.graphify/`, `.graphify_*.json`). Never share an unchecked index externally; do not assume graphs synchronize across environments.

**Graphify published CLI installation and graph-output paths are vendor documentation, not yet tested against Averon here.** Avoid quoting vendor performance benchmarks as project measurements.

## Hosted Graphify — optional future connection

Official endpoint documentation: https://github.com/Graphify-Labs/graphify-mcp

Endpoint: `https://api.graphify.com/mcp`; browser OAuth and compatible HTTP MCP client required. Enabling means choosing a Graphify account/workspace and connecting a GitHub repository for hosted indexing. Treat this as an **external sharing/authorization decision**, not automatically approved just because GitHub is connected to ChatGPT. Never place OAuth tokens/API keys in the repo.

For the current ChatGPT session, a plugin-directory lookup did **not** expose an installable Graphify integration. Do not claim ChatGPT and Claude share a graph until **both** clients independently query the same indexed repository and successfully retrieve a shared test note. If unavailable, use GitHub issues and PRs for inter-agent handoff.

## Ponytail — controlled experiment only

Source: https://github.com/DietrichGebert/ponytail

Do not enable arbitrary shell hooks, globally inject compression rules, or automatically route model requests. Developers may inspect and test Ponytail locally in an isolated checkout after permission. Compare equal-scope tasks with/without it using token consumption, completion time, code and build correctness, and rework. Disable if results are ambiguous. Do **not** impose token-saving instructions on safety-critical save/progression code.

## OmniRoute — not installed

Defer gateways and model routing until there is a demonstrated, quantified model-cost or availability need. Do not silently enable third-party billing.

## ChatGPT-side setup and verification

The GitHub connector is available for reading PRs/issues and proposing documentation. Graphify was not available in the current ChatGPT plugin lookup. This chat cannot silently install code or authenticate another agent's local environment.

Verification checklist (each independent agent records PASS/FAIL/UNTESTED with actual evidence):

- [ ] Skill path discovery and invocation in local Claude Code
- [ ] Skill path discovery and invocation in local Codex
- [ ] Graphify CLI installed locally and queried successfully at a known SHA
- [ ] No graph build artifacts, ROMs, saves or secrets added to git
- [ ] ChatGPT Graphify account connection verified (optional, currently UNTESTED)
- [ ] One GitHub issue/PR handoff read by another agent
- [ ] No conflicts with claimed QUEST or SCRIPTED-BATTLE production paths
- [ ] If experimenting with Ponytail, actual before/after measurement recorded

## Two-step rollout

**Phase 1 (safe default):** merge documentation and skills after code review; independently verify skills discovery; leave every third-party installation and paid service disabled.

**Phase 2 (opt-in):** a developer installs local Graphify, indexes the repository and benchmarks queries. If a shared cross-runtime hosted graph is needed, ask the owner before authorizing hosted repo access. Enable Ponytail trial only with reviewed hooks and rollback instructions.

Do not claim the full multi-agent environment has been validated before each agent confirms its own setup.
