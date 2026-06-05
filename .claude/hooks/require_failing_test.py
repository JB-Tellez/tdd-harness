#!/usr/bin/env python3
"""PreToolUse hook: keep production code test-driven (RED-before-GREEN, with a
refactor allowance).

This is the "gate" hook. It fires before every Edit/Write and asks one
question: *is the agent allowed to touch production code right now?* The TDD
answer is "only when a test justifies it." So:

  - Editing a test file?              -> always allowed (that's how you get RED)
  - Editing src/ with a test failing? -> allowed (you're in GREEN, making it pass)
  - Editing src/ while green?         -> allowed AS A REFACTOR. A green suite
                                         means >=1 passing test exists, so
                                         behaviour-preserving restructuring is
                                         legitimate. The hook cannot tell a real
                                         refactor from new untested code written
                                         while green; the skill's REFACTOR gate
                                         owns that confirmation.
  - Editing src/ with NO tests at all -> DENIED -- nothing drives the edit and
                                         there is nothing to refactor; write a
                                         failing test first.

Doing this as a hook, not a skill instruction, still makes one thing a
constraint the agent cannot violate: you may never write production code with
zero tests in play. The narrower "RED-before-GREEN for *new behaviour*" rule
now lives in the skill's REFACTOR gate (judgment), because once green edits are
allowed the hook can no longer distinguish a refactor from a new feature.
Discipline can live in someone's judgment or in the system; this hook keeps the
hard floor in the system and delegates the refactor/feature call to the gate.

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
    tests_exist,
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


# Reasons for the two deny states. Kept as module constants so the decision
# logic (decide) stays pure and unit-testable.
NONE_REASON = (
    "No tests exist, so nothing is driving this production edit and there is "
    "nothing to refactor. Write a single failing test first (RED), confirm it "
    "fails, then implement. (Enforced by the require_failing_test.py PreToolUse "
    "hook.)"
)

ERROR_REASON = (
    "Could not determine test state -- pytest did not run a suite (missing "
    "dependency, import error, or collection failure), so the gate is failing "
    "closed. Fix the test runner before editing production code."
)


def decide(state, tests_exist):
    """Map a test-suite state to an allow/deny decision for a production edit.

    Returns ``(allowed, reason)`` -- ``reason`` is ``None`` when allowed.

    The rule keeps production code test-driven without forbidding the refactor
    step of red-green-refactor:

      red   -> allow : a failing test is driving this edit (the GREEN phase).
      green -> allow : the suite is green, so >=1 passing test exists; treat the
                       edit as a REFACTOR. Behaviour-preserving restructuring is
                       legitimate while green. The hook cannot tell a genuine
                       refactor from new untested behaviour written green -- the
                       skill's REFACTOR gate owns that confirmation.
      none  -> deny  : zero tests exist; nothing drives the edit and there is
                       nothing to refactor. Write a failing test first.
      error -> allow if tests_exist, deny otherwise : if test files exist but
                       pytest can't run them (import error, dependency missing),
                       treat as RED -- tests exist and are driving the edit,
                       they're just currently broken. If no tests exist at all,
                       fail closed.
    """
    if state in ("red", "green"):
        return True, None
    if state == "error" and tests_exist:
        return True, None
    if state == "none":
        return False, NONE_REASON
    return False, ERROR_REASON


def main():
    payload = read_tool_input()
    project_dir = project_dir_from_env()

    # Gate FIRST: stay inert unless this project opted into tdd-harness. As a
    # global plugin this hook fires everywhere; in a repo that didn't opt in
    # we must allow silently and never run pytest. (See workflow_enabled.)
    if not workflow_enabled(project_dir):
        allow()

    path = edited_path(payload)

    # Only production code is gated. Tests, docs, config -- all free.
    if not is_production_code(path, project_dir):
        allow()

    state, output = run_pytest(project_dir)
    test_files_exist = tests_exist(project_dir)
    allowed, reason = decide(state, test_files_exist)

    # red  -> a failing test is driving this edit (GREEN phase).
    # green -> >=1 passing test exists; treat as REFACTOR. The skill's REFACTOR
    #          gate is responsible for confirming it's behaviour-preserving, not
    #          new untested code -- the hook can't tell those apart.
    # error with tests -> tests exist but pytest can't run them; treat as RED.
    if allowed:
        allow()

    # error carries the pytest output so the broken runner can be fixed.
    if state == "error":
        deny(reason + "\n\npytest output:\n" + output.strip())

    # none -> no tests in play; nothing drives the edit and nothing to refactor.
    deny(reason)


if __name__ == "__main__":
    main()
