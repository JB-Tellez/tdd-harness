# AGENTS.md

This document describes the agents, personas, and TDD process for this project. These definitions are tool-agnostic and can be integrated into any AI development environment.

## Agent definitions

**`tdd-developer`** — The simulated developer persona that reviews TDD gates in autonomous runs.

Located in `.claude/agents/tdd-developer.md`. This persona is invoked at each gate (RED, GREEN, REFACTOR, deglaze) by the `auto-tdd` skill to provide independent architectural review and implementation feedback. The persona is defined once and reused across gates to maintain consistency.

The key idea: a fresh subagent that *didn't write the test* can notice architectural commitments the original agent might miss. This asymmetry is the core discipline that survives autonomous runs.

## TDD process

The `auto-tdd` skill implements strict red-green-refactor with a decision log. See `.claude/skills/auto-tdd/SKILL.md` for the full process specification — it's tool-agnostic and describes:

- Writing one failing test (RED)
- Minimal code to pass (GREEN)  
- Optional refactoring (REFACTOR)
- Pre-commit engagement check (deglaze)
- Decision logging (DEV_LOG.md)

Parent skills (`tdd` and `deglaze`) are also in `.claude/skills/` for reference.

## Integration

For **Claude Code**: The skills and agents are already wired up in `.claude/settings.json` (permission allowlist) and `.claude/hooks/` (validation scripts). Run `/auto-tdd <spec>` to start an autonomous run.

For **other tools**: Read `.claude/skills/auto-tdd/SKILL.md` as the process spec. Key validation rules from `.claude/hooks/`:
- `enforce_canonical_pytest.py` — pytest must be invoked as `.venv/bin/python -m pytest` (no wrapping, no `PYTHONPATH=`, no activation)
- `require_failing_test.py` — production edits require a failing test first
- `report_test_state.py` — test state is reported after each edit

## Setup

Activate the virtual environment before running anything:

```sh
source .venv/bin/activate
```

If `.venv/` is missing, recreate it:

```sh
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

## Running tests

```sh
.venv/bin/python -m pytest
```

## Adding dependencies

```sh
pip install <package> && pip freeze > requirements.txt
```
