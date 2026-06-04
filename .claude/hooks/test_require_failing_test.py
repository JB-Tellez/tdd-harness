"""Tests for the RED-before-GREEN gate's allow/deny decision.

These pin the core rule the gate enforces once it's active (workflow enabled
and a production-code edit is in flight): which test-suite states permit a
production edit. The decision is factored into the pure `decide(state)` so it
can be checked without driving pytest or the stdin/exit plumbing.

Run from this folder:  python -m pytest test_require_failing_test.py
"""

import require_failing_test as gate


def test_red_allows_green_phase_edit():
    # A failing test is driving the change -- the classic GREEN step.
    assert gate.decide("red") == (True, None)


def test_green_allows_refactor():
    # Green means >=1 passing test exists; editing src/ is permitted as a
    # refactor. (The skill's REFACTOR gate, not the hook, confirms it really is
    # behaviour-preserving and not new untested code.)
    allowed, reason = gate.decide("green")
    assert allowed is True
    assert reason is None


def test_none_denies_when_no_tests_exist():
    # Zero tests: nothing drives the edit and nothing to refactor -> blocked.
    allowed, reason = gate.decide("none")
    assert allowed is False
    assert reason


def test_error_denies_fail_closed():
    # A broken runner must not silently disable the gate.
    allowed, reason = gate.decide("error")
    assert allowed is False
    assert reason
