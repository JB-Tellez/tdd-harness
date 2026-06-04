# tdd-harness — spec-driven TDD template

A copyable Python project template for building from Gherkin specs using autonomous, gated TDD.

## Quick start

```sh
cp -R . ~/my-new-project
cd ~/my-new-project
./setup.sh

# Now: edit features/*.feature with your scenarios
# Then: open Claude Code in this folder and type /auto-tdd
```

## What it does

- **RED:** Writes one failing test per scenario
- **GREEN:** Minimal code to pass
- **REFACTOR:** Optional cleanup (reviewer decides)
- **Thoughtful commit:** Pre-commit engagement check ("what changed and why?"), then logs the cycle with decision rationale

One small cycle per scenario, end-to-end, with a decision log you review after.

## Structure

**You provide:**
- `features/*.feature` — Your Gherkin scenarios

**Gets generated:**
- `src/` — Production code (one cycle per scenario)
- `tests/` — Tests (one per scenario)
- `DEV_LOG.md` — Decision log from the run

**The harness (don't edit):**
- `.claude/skills/` — TDD process definition
- `.claude/agents/` — Simulated developer persona
- `.claude/hooks/` — Validation (RED-before-GREEN, canonical pytest)
- `.claude/settings.json` — Pre-approved commands so runs proceed unattended (see Advanced → Why no prompts)
- `spec-mcp/` — Makes your scenarios queryable to the agent so that they map well to unit tests.

See [AGENTS.md](AGENTS.md) for details on the process and personas.

## Important: open Claude Code in this folder

`.mcp.json` and the hooks resolve paths relative to the project root. Open Claude Code with **this directory** as the project root, not a parent folder.

## Advanced

### Adapting to non-Python projects

The workflow is language-agnostic. Two pieces need editing:

- **Hooks** (`.claude/hooks/`) — Currently shell out to `pytest`. For Node, edit the runner in `_testlib.py` (e.g., `jest`/`vitest`); the RED-before-GREEN *logic* stays the same.
- **Spec MCP** (`spec-mcp/spec_lib.py`) — Currently greps for `def test_`. For another language, change `collect_test_names` to match that language's test convention.

Everything else — skills, agent, settings — is text the agent reads unchanged.

### Verifying the harness

The MCP server ships with self-tests:

```sh
cd spec-mcp && ../.venv/bin/python -m pytest test_spec_lib.py
```

Run these in a fresh copy before adding anything to confirm the harness itself works.

### How it works: RED-before-GREEN

The hook system prevents a common mistake: writing code without a failing test first. When `.claude/tdd-harness.json` has `{"enforce": true}`, a `PreToolUse` hook blocks any edit to `src/` unless:

- The test suite is currently failing (there's a test to drive), *or*
- The current edit is a refactor (suite is green and we're changing structure, not behavior)

This is a load-bearing constraint: it's how autonomous runs stay disciplined without a human at the gate.

**Hook gating.** The hooks are inert unless `.claude/tdd-harness.json` contains `{"enforce": true}`. The template ships it on. To disable, set `"enforce": false` (or delete the file). This matters for the future plugin scenario: a globally-enabled plugin would otherwise fire its hooks in every repo you open. The gate keeps it dormant everywhere except where you said "enforce."

### Integration with other tools

The core TDD process in `.claude/skills/auto-tdd/SKILL.md` is tool-agnostic and documents the discipline in plain English. Other tools (Codex, AntiGravity, etc.) can read it and implement the same workflow. The validation rules in `.claude/hooks/` are Python scripts that can be wired into any AI development environment.

See [AGENTS.md](AGENTS.md) for how to integrate into non-Claude-Code tools.

### Future: promoting to a plugin

**Not done yet — this is the planned next step.** A Claude Code plugin would let you install once and use in any project, with no file-copying. The structure would change slightly (moving skills/agents/hooks up from `.claude/`), but the workflow stays the same. The key difference: path variables would distinguish `${CLAUDE_PLUGIN_ROOT}` (plugin files) from `${CLAUDE_PROJECT_DIR}` (project files), so the bundled spec MCP and hooks can operate on different projects.

When we do this, all the hard problems are solved: hook gating already works, the MCP already accepts `--features`/`--tests` flags to point at any project, and the skills are already readable text. The conversion is mechanical.

### Why no prompts

A `/auto-tdd` run does the same few operations repeatedly (run pytest, read/write, commit, query specs). The template pre-approves exactly those in `.claude/settings.json`, so the run proceeds without stopping to ask.

Two things make it work:

1. **Canonical pytest command** — Tests always run as `.venv/bin/python -m pytest` (from project root, no `PYTHONPATH=`, no `source`, no bare `python`). This exact form is pre-approved; drift forces a new prompt. A `PreToolUse` hook blocks non-canonical forms and tells the agent the right way, so drift self-corrects instead of prompting.

2. **`setup.sh` runs one-time operations first** — venv, git init, `DEV_LOG.md` — so they never prompt mid-run.

#### Why not just bypass all prompts

The template has a targeted allowlist, not a blanket bypass (`bypassPermissions`). A template copied into project after project shouldn't carry a setting that lets commands run unchecked. The trade-off is honest: an allowlist is never complete, so the agent will occasionally hit an unanticipated command. When it does, approve it in the moment, then add it to `permissions.allow` if it's genuinely part of the workflow. The allowlist converges by use.

You can tell the agent to edit the file directly (e.g., "add this command to the allowlist") and Claude Code reloads rules immediately.

For true throwaway trial work, you can set `"defaultMode": "bypassPermissions"` in `.claude/settings.local.json` (git-ignored), but that's an escape hatch, not how the workflow is meant to run.

#### Discipline isn't bypassed

Pre-approving permissions removes friction, not discipline. The RED-before-GREEN hook still fires regardless and can still block, so "no prompts" ≠ "no gates."
