#!/usr/bin/env python3
"""PostToolUse hook: report red/green after each production edit.

This is the "observer" hook -- the counterpart to require_failing_test.py.
Where the gate hook *blocks*, this one never blocks anything. It runs after an
Edit/Write to src/ lands, runs the suite, and feeds the current red/green state
back into the agent's context so the next step is taken with eyes open.

The teaching contrast is the whole reason both hooks ship together: hooks come
in two flavors. A *gate* (PreToolUse, can deny) enforces a rule. An *observer*
(PostToolUse, advisory) tightens the feedback loop. Same machinery, different
job -- and students should be able to feel the difference by reading these two
files next to each other.

Contract (Claude Code PostToolUse hooks): the tool has already run, so we
cannot undo it. We surface information via additionalContext, which is injected
back for the model to read. Exit 0 always.
"""

import json
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _testlib import (  # noqa: E402
    edited_path,
    is_production_code,
    project_dir_from_env,
    read_tool_input,
    run_pytest,
    workflow_enabled,
)


def emit(context):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": context,
                }
            }
        )
    )
    sys.exit(0)


def summarize(state, output):
    """Turn a classified pytest run into a one-line state the agent can act on."""
    # Last non-empty line of pytest -q is its summary (e.g. "1 passed in 0.01s").
    tail = ""
    for line in reversed(output.splitlines()):
        if line.strip():
            tail = line.strip()
            break
    if state == "green":
        return f"GREEN — all tests pass. ({tail})"
    if state == "red":
        return f"RED — at least one test is failing. ({tail})"
    if state == "none":
        return "No tests collected — nothing pins this code yet."
    return f"Could not run the suite — pytest did not produce a result. ({tail})"


def main():
    payload = read_tool_input()
    project_dir = project_dir_from_env()

    # Gate FIRST: stay inert (silent, no test run) unless this project opted
    # into tdd-harness. See workflow_enabled in _testlib.
    if not workflow_enabled(project_dir):
        sys.exit(0)

    path = edited_path(payload)

    # Only bother running tests when production code changed.
    if not is_production_code(path, project_dir):
        sys.exit(0)

    state, output = run_pytest(project_dir)
    emit("Test state after this edit: " + summarize(state, output))


if __name__ == "__main__":
    main()
