# spec-tdd — a portable spec-driven TDD harness

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
| `skills/auto-tdd/` | The autonomous TDD process (red → green → refactor → deglaze → commit) |
| `skills/tdd/`, `skills/deglaze/` | The parent skills it builds on |
| `.claude/agents/tdd-developer.md` | The "simulated developer" subagent that reviews each gate |
| `.claude/hooks/` + `.claude/settings.json` | RED-before-GREEN gate + test-state observer |
| `spec-mcp/` + `.mcp.json` | Exposes your `features/` as queryable tools |
| `AGENTS.md`, `pytest.ini`, `pyrightconfig.json`, `requirements.txt` | Conventions + tooling config |

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
cp -R templates/spec-tdd ~/my-new-project
cd ~/my-new-project

# 2. Set up the environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r spec-mcp/requirements.txt   # only if you want the spec MCP

# 3. Replace features/example.feature with your real behaviors
#    (add as many .feature files as you like)

# 4. Open Claude Code IN THIS FOLDER (important — see note below), then:
#    /auto-tdd
```

The agent reads your scenarios, then drives one TDD cycle per scenario. When
it finishes, review `DEV_LOG.md` and the generated code — see the course's
`docs/verifying-an-auto-tdd-run.md` for a verification checklist.

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
cd spec-mcp && python -m pytest test_spec_lib.py
```

These are self-contained (they write tiny temp specs) and should pass in a
fresh copy before you add anything.
