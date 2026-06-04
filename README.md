# tdd-harness — a portable spec-driven TDD harness

This is a **copyable starter** for building a Python project from a Gherkin
spec using autonomous, gated TDD. Drop in your feature files, point Claude
Code at the folder, run `/auto-tdd`, and the source and tests get generated —
one small red-green-refactor cycle per scenario, with a decision log you
review at the end.

It's distilled from the `auto-tdd/end` reference in the AI-345 course. Same
workflow, with the example app removed so you start from your own specs.

## What's harness vs. what you provide

The point of the template is this split:

**The harness (don't edit unless you mean to):**

| Path | What it is |
| --- | --- |
| `.claude/skills/auto-tdd/` | The autonomous TDD process (red → green → refactor → deglaze → commit) |
| `.claude/skills/tdd/`, `.claude/skills/deglaze/` | The parent skills it builds on |
| `.claude/agents/tdd-developer.md` | The "simulated developer" subagent that reviews each gate |
| `.claude/hooks/` | RED-before-GREEN gate + test-state observer + canonical-pytest enforcer (scripts) |
| `.claude/settings.json` | Wires the hooks + pre-approves the run's commands (`permissions.allow`) so it runs unattended |
| `.claude/tdd-harness.json` | **Opt-in switch** — the hooks only act when `{"enforce": true}` is here |
| `spec-mcp/` + `.mcp.json` | Exposes your `features/` as queryable tools |
| `AGENTS.md`, `pytest.ini`, `pyrightconfig.json`, `requirements.txt` | Conventions + tooling config |

> **Hook gating.** The hooks are inert unless `.claude/tdd-harness.json` contains
> `{"enforce": true}`. The template ships it on, so a copied project enforces
> RED-before-GREEN out of the box. This matters most for the *plugin* future
> (below): a globally-enabled plugin would otherwise fire its hooks in every
> repo you open and block edits in projects that never opted in. The gate keeps
> it dormant everywhere except where you said `enforce`. To disable in a copied
> project, set `"enforce": false` (or delete the file).

## Running unattended (few/no approval prompts)

A `/auto-tdd` run does the same handful of operations over and over — run
pytest, read/write files, git add/commit, and query the `spec` MCP server. The
template pre-approves exactly those in `.claude/settings.json`
(`permissions.allow`, including `mcp__spec` for all the spec server's tools),
so the run proceeds without stopping to ask. Two things make this actually
work:

1. **The skill always runs the suite the same way: `.venv/bin/python -m pytest`**
   (from the project root, no `PYTHONPATH=`, no `source`, no bare `python`).
   Calling the venv interpreter by path means it works with no activation —
   bare `python` would resolve to system python (no pytest) unless a shell
   happened to activate the venv first. Claude Code's "don't ask again" matches
   a *command prefix*, so the one allowlisted form
   `Bash(.venv/bin/python -m pytest:*)` covers every test run. Drift — a stray
   `PYTHONPATH=src`, a `source .venv/...`, bare `python`, an explicit test
   path — defeats the match and forces a fresh prompt. The skill states this as
   a hard rule, and a `PreToolUse` hook (`enforce_canonical_pytest.py`)
   *enforces* it: any non-canonical pytest command is blocked with a message
   telling the agent the right form, so drift self-corrects instead of
   prompting. (Reading files is likewise pushed to the Read tool, not
   `cat`/`find -exec`, which can't be auto-approved.)
2. **`setup.sh` does the one-time operations** (venv, `git init`, creating
   `DEV_LOG.md`) *before* the run, so they never prompt mid-run.

### Why a targeted allowlist, not a blanket bypass

Claude Code does offer a way to skip *every* prompt — `"defaultMode":
"bypassPermissions"` (the "YOLO" switch). **We deliberately don't use it here,
and don't teach it.** A template that gets copied into project after project
shouldn't carry a setting that lets the agent run any command unchecked; the
blast radius of one wrong call is too large for something meant to be reused.

So instead we enumerate the specific commands the workflow needs and approve
only those. The honest trade-off: an allowlist is never complete. The agent
will occasionally reach for a command we didn't anticipate, and that one will
prompt. We treat that as expected — approve it in the moment, and if it's a
command the workflow genuinely needs every run, add it to `permissions.allow`
then. The allowlist converges by use, not by trying to predict everything up
front. Prefer this narrowing-over-time approach to flipping on a bypass.

**Adding rules mid-session.** You don't have to stop and hand-edit JSON. When a
command prompts and you expect to need it again, you can just tell the agent in
plain language — e.g. *"add `.venv/bin/python -m pytest` to the allowlist in
`.claude/settings.json`"* — and it edits `permissions.allow` for you. Claude
Code reloads permission rules immediately, so the new rule takes effect for the
rest of the session without a restart. (The prompt's own "Yes, and don't ask
again" option also persists the rule, though which file it writes to isn't
documented — instructing the agent to edit a named file is the predictable
way.) Each project will surface its own commands this way, so expect to grow
the list a little the first few runs on a new spec.

Where to put the rule: a rule the whole team should trust goes in the
committed `.claude/settings.json`; a personal or still-being-vetted one goes in
the git-ignored `.claude/settings.local.json`. When in doubt, start local and
promote it to the shared file once you're confident.

(If you truly want zero prompts for a *throwaway* trial in a disposable
directory, `bypassPermissions` exists — set it in the git-ignored
`.claude/settings.local.json` so it never ships with the template. But that's
an escape hatch for scratch work, not how the workflow is meant to run.)

**The gating hooks still fire regardless.** Pre-approving permissions does not
disable the RED-before-GREEN hook — hooks run before permission rules and can
still block. So "no prompts" removes *friction*, not *discipline*.

**What you provide / what gets generated:**

| Path | Role |
| --- | --- |
| `features/*.feature` | **Input** — you write these (replace `example.feature`) |
| `src/` | **Output** — production code, generated per cycle |
| `tests/` | **Output** — one test per scenario, generated per cycle |
| `DEV_LOG.md` | **Output** — the run's decision log (created on first run) |

## Using it

```sh
# 1. Copy the template to your new project
cp -R templates/tdd-harness ~/my-new-project
cd ~/my-new-project

# 2. Set up the environment (venv + deps + a selftest)
./setup.sh

# 3. Replace features/example.feature with your real behaviors
#    (add as many .feature files as you like; re-run ./setup.sh to confirm
#     they're picked up)

# 4. Open Claude Code IN THIS FOLDER (important — see note below), then:
#    /auto-tdd
```

`setup.sh` is idempotent — re-run it any time (e.g. after adding feature
files) to reinstall and re-print the scenarios the harness can see.

The agent reads your scenarios, then drives one TDD cycle per scenario. When
it finishes, review `DEV_LOG.md` and the generated code — see the course's
`docs/verifying-an-auto-tdd-run.md` for a verification checklist.

<details>
<summary>What <code>setup.sh</code> does (if you'd rather run it by hand)</summary>

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r spec-mcp/requirements.txt   # only if you want the spec MCP
python spec-mcp/spec_server.py --selftest  # confirms it sees your features
```
</details>

## Important: open Claude Code with this folder as the project root

`.mcp.json` resolves the MCP server via `${CLAUDE_PROJECT_DIR:-.}`, and the
hooks resolve paths the same way. Both assume **this directory** is the
project root. If you open Claude Code one level up, the MCP server and hooks
won't find the venv or the specs.

## Adapting to a non-Python project

The workflow is language-agnostic; two pieces are not, and would need editing:

- **The hooks** (`.claude/hooks/`) shell out to `pytest`. For Node, swap the
  runner invocation in `_testlib.py` (e.g. `jest`/`vitest`) — the
  RED-before-GREEN *logic* is unchanged, only the command and exit-code
  handling differ.
- **The spec MCP** (`spec-mcp/spec_lib.py`) greps for `def test_` to find
  tests. For another language, change `collect_test_names` to match that
  test-naming convention.

Everything else — the skills, the agent, the settings — is text the agent
interprets and carries over unchanged.

## Verifying the harness itself

The MCP logic ships with its own tests:

```sh
cd spec-mcp && ../.venv/bin/python -m pytest test_spec_lib.py
```

These are self-contained (they write tiny temp specs) and should pass in a
fresh copy before you add anything. (Calling `../.venv/bin/python` by path
works whether or not you've activated the venv.)

## Future: promoting this template to a Claude Code plugin

**Not done yet — this is the planned next step.** Copying the folder works, but
a *plugin* would make the harness installable once and available in every
project, with no file-copying and version management built in. When we do
this, here's the shape and the one real gotcha.

### Why promote it

- Install once (`claude plugin install tdd-harness`), use in any repo — no `cp -R`.
- Version-managed: pin a version, update centrally.
- The skills become namespaced (`/tdd-harness:auto-tdd`), so they don't collide
  with a project's own skills.

### The structure change (project layout → plugin layout)

A plugin keeps its components at the plugin *root* (not under `.claude/`), with
a manifest at `.claude-plugin/plugin.json`:

```
tdd-harness/                      # plugin root
├── .claude-plugin/plugin.json    # manifest (name, version, description)
├── skills/{auto-tdd,tdd,deglaze}/  # moved up from .claude/skills/ (same files)
├── agents/tdd-developer.md       # moved up from .claude/agents/
├── hooks/hooks.json              # the hook config from .claude/settings.json
├── .claude/hooks/*.py            # the hook scripts (can stay; see paths below)
├── .mcp.json                     # at plugin root
└── spec-mcp/                     # bundled MCP server (unchanged)
```

A minimal manifest:

```json
{
  "name": "tdd-harness",
  "version": "0.1.0",
  "description": "Autonomous spec-driven TDD: features in, src + tests out."
}
```

### The one real gotcha: two path variables, not one

This is the crux, and it's *specific to a file-generating workflow like this
one*. Today the template resolves everything via `${CLAUDE_PROJECT_DIR:-.}` —
both the bundled scripts and the project it operates on are the same folder. In
a plugin they are **two different places**, and the config must distinguish:

- **`${CLAUDE_PLUGIN_ROOT}`** — where the plugin's own files live (the hook
  scripts, the MCP server, `spec_lib.py`). Stays the same across every project.
- **`${CLAUDE_PROJECT_DIR}`** — the repo the user is currently in, where
  `features/` is read and `src/`/`tests/` get generated. Different per project.

So the conversions are:

- **MCP** (`.mcp.json`): launch the server from the plugin, but point its
  `--features`/`--tests` at the project.
  ```json
  {
    "mcpServers": {
      "spec": {
        "command": "${CLAUDE_PLUGIN_ROOT}/spec-mcp/.venv/bin/python",
        "args": [
          "${CLAUDE_PLUGIN_ROOT}/spec-mcp/spec_server.py",
          "--features", "${CLAUDE_PROJECT_DIR}/features",
          "--tests", "${CLAUDE_PROJECT_DIR}/tests"
        ]
      }
    }
  }
  ```
  (`spec_server.py` already accepts `--features`/`--tests`, so no code change —
  this is exactly why those flags exist.)

- **Hooks** (`hooks/hooks.json`): invoke the bundled script via
  `${CLAUDE_PLUGIN_ROOT}` but run it against the current project. The hooks
  read `CLAUDE_PROJECT_DIR` from the environment already (`project_dir_from_env`
  in `_testlib.py`), so they keep working — just change the script path:
  ```json
  { "type": "command",
    "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/.claude/hooks/require_failing_test.py\"" }
  ```

- **Skills / agent**: move the files up to `skills/` and `agents/`; their
  *content* is unchanged. Anything inside them that points at the project still
  uses `${CLAUDE_PROJECT_DIR}`.

### Distribution

Host the plugin in a git repo and reference it from a `marketplace.json`; users
run `claude plugin marketplace add <url>` then `claude plugin install tdd-harness`.
For internal/personal use, `claude plugin init` scaffolds a skills-dir plugin
that loads with no marketplace at all — the simplest first step.

### Watch-outs when we do it

- **The MCP needs its own venv inside the plugin** (`${CLAUDE_PLUGIN_ROOT}/spec-mcp/.venv`),
  since the project's venv may not have `mcp` installed. Decide whether to
  bundle/bootstrap it.
- **Hook gating — already handled.** As a globally-enabled plugin the hooks
  would fire in *every* project, including non-Python ones. This is solved:
  both hooks check `workflow_enabled()` (in `_testlib.py`) first and stay inert
  unless the current project has `.claude/tdd-harness.json` with
  `{"enforce": true}`. We chose an explicit opt-in over auto-detecting pytest
  because the bad failure mode — wrongly *blocking* edits in a stranger's repo
  — is far worse than wrongly staying silent, so the gate errs toward OFF
  (missing/false/malformed config all disable). Covered by
  `.claude/hooks/test_gating.py`.
- **Always ship an explicit manifest** to control the `name` (and thus the
  skill namespace) rather than relying on directory-name auto-discovery.
