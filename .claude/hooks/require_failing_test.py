#!/usr/bin/env python3
"""PreToolUse hook: enforce RED-before-GREEN.

This is the "gate" hook. It fires before every Edit/Write and asks one
question: *is the agent allowed to touch production code right now?* The TDD
answer is "only if there is a failing test driving the change." So:

  - Editing a test file?              -> always allowed (that's how you get RED)
  - Editing src/ with a test failing? -> allowed (you're in GREEN, making it pass)
  - Editing src/ with all green?      -> DENIED -- write a failing test first

The point of doing this as a hook, not a skill instruction, is that it's not a
norm the agent is asked to follow -- it's a constraint it cannot violate. That
distinction is the lesson: discipline can live in someone's judgment, or it can
live in the system. This hook is the system version.

Contract (Claude Code PreToolUse hooks): read the tool payload on stdin; to
block, print a JSON decision object and exit 0; to allow, exit 0 with no
decision. We use the structured form so the agent receives a reason it can act
on.
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


def allow():
    # No output needed to allow; explicit empty decision keeps intent obvious.
    sys.exit(0)


def deny(reason):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def main():
    payload = read_tool_input()
    project_dir = project_dir_from_env()

    # Gate FIRST: stay inert unless this project opted into spec-tdd. As a
    # global plugin this hook fires everywhere; in a repo that didn't opt in
    # we must allow silently and never run pytest. (See workflow_enabled.)
    if not workflow_enabled(project_dir):
        allow()

    path = edited_path(payload)

    # Only production code is gated. Tests, docs, config -- all free.
    if not is_production_code(path, project_dir):
        allow()

    state, output = run_pytest(project_dir)

    # A genuinely failing test means we're legitimately in GREEN, writing code
    # to make it pass. That's the one state where editing src/ is allowed.
    if state == "red":
        allow()

    # green / none -> nothing red is driving this edit: a RED-before-GREEN
    # violation. Block and explain.
    if state in ("green", "none"):
        deny(
            "RED-before-GREEN: there is no failing test, so production code "
            "may not be edited yet. Write a single failing test that drives "
            "this change first, confirm it fails, then implement. (Enforced "
            "by the require_failing_test.py PreToolUse hook.)"
        )

    # error -> pytest could not run a suite. Fail CLOSED: a broken test runner
    # must not silently disable the gate. Surface the failure so it gets fixed.
    deny(
        "Could not determine test state -- pytest did not run a suite "
        "(missing dependency, import error, or collection failure), so the "
        "RED-before-GREEN gate is failing closed. Fix the test runner before "
        "editing production code.\n\npytest output:\n" + output.strip()
    )


if __name__ == "__main__":
    main()
