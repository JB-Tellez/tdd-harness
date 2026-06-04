#!/usr/bin/env python3
"""Spec MCP server -- exposes Gherkin feature files as queryable tools.

The teaching point: today the auto-tdd skill reads the raw .feature text into
context and re-parses it by eye every time it needs the scenario list. That's
*context-stuffing*. This server turns the same specs into a small queryable
API -- the agent asks precise questions and gets structured answers back. That
is what an MCP is *for*: restructuring the model's context from a file-dump
into tools.

All logic lives in spec_lib.py; this file is only the MCP wiring, so the
interesting part stays readable on its own.

Scope: project-scoped on purpose. Pointed at a single app's features and
tests (default: this folder's todo specs + tests), so it never cross-matches
one app's scenarios to another app's tests. Override with --features/--tests.

Run standalone for a sanity check:
    python spec_server.py --selftest

Wire into Claude Code via .mcp.json (see this folder's .mcp.json).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from spec_lib import (
    collect_test_names,
    load_scenarios,
    match_scenarios_to_tests,
)
from spec_lib import scenarios_without_tests as gaps_for

# Resolved at startup from CLI args; default to this project's own dirs.
# In the template the project is self-contained: features/ and tests/ live at
# the project root (the parent of this spec-mcp/ folder), not in a shared
# repo-level features/ dir. Override either with --features / --tests.
_HERE = Path(__file__).resolve().parent
_PROJECT = _HERE.parent                       # the project root
FEATURES_ROOT = _PROJECT / "features"
TESTS_DIR = _PROJECT / "tests"

mcp = FastMCP("spec")


@mcp.tool()
def list_features() -> list[dict]:
    """List the features in scope, each with its scenario count.

    Orientation tool: the work-list at a glance, without reading any file.
    """
    scenarios = load_scenarios(FEATURES_ROOT)
    by_file: dict[str, dict] = {}
    for s in scenarios:
        entry = by_file.setdefault(
            s.feature_file, {"feature": s.feature, "feature_file": s.feature_file, "scenario_count": 0}
        )
        entry["scenario_count"] += 1
    return list(by_file.values())


@mcp.tool()
def list_scenarios(feature_file: str | None = None) -> list[dict]:
    """List scenarios (optionally filtered to one feature file), with steps.

    Replaces "read the .feature file and enumerate the scenarios" with a
    structured fetch. Pass a feature_file (as returned by list_features) to
    narrow to one feature.
    """
    scenarios = load_scenarios(FEATURES_ROOT)
    if feature_file:
        scenarios = [s for s in scenarios if s.feature_file == feature_file]
    return [s.as_dict() for s in scenarios]


@mcp.tool()
def get_scenario(name: str) -> dict | None:
    """Fetch one scenario by (case-insensitive) title, with its full steps.

    The auto-tdd loop pulls a single scenario this way to drive one cycle.
    Returns null if no scenario matches.
    """
    wanted = name.strip().lower()
    for s in load_scenarios(FEATURES_ROOT):
        if s.name.lower() == wanted:
            return s.as_dict()
    return None


@mcp.tool()
def coverage_report() -> list[dict]:
    """Best-effort scenario-to-test match for every scenario in scope.

    HEURISTIC, name-matching only -- no test execution. Each entry carries a
    `confidence` ("high"/"low"/"none") and `score`. Treat it as a guess to
    verify, never a coverage guarantee. The `test_name` pointer can be wrong
    even when `confidence` is "high" (two similarly-named tests); the coverage
    *verdict* is more reliable than the specific pointer.
    """
    scenarios = load_scenarios(FEATURES_ROOT)
    tests = collect_test_names(TESTS_DIR)
    return [m.as_dict() for m in match_scenarios_to_tests(scenarios, tests)]


@mcp.tool()
def scenarios_without_tests() -> list[dict]:  # noqa: F811 (tool name mirrors lib)
    """Scenarios with no high-confidence matching test -- the coverage gaps.

    This is the keystone tool: it turns Step 1 of the verification guide
    ("map every scenario to a real test") from a manual side-by-side read into
    a single query. Includes LOW-confidence matches deliberately -- a weak
    match is something to verify, not assume. Same heuristic caveat as
    coverage_report: it surfaces doubt, it doesn't prove coverage.
    """
    scenarios = load_scenarios(FEATURES_ROOT)
    tests = collect_test_names(TESTS_DIR)
    return [m.as_dict() for m in gaps_for(scenarios, tests)]


def _selftest() -> int:
    """Parse + match against the configured paths and print a summary.

    Lets you confirm the server sees the right files before wiring it into
    Claude Code -- no MCP client required.
    """
    scenarios = load_scenarios(FEATURES_ROOT)
    tests = collect_test_names(TESTS_DIR)
    print(f"features root: {FEATURES_ROOT}")
    print(f"tests dir:     {TESTS_DIR}")
    print(f"parsed {len(scenarios)} scenario(s), found {len(tests)} test(s)")
    gaps = gaps_for(scenarios, tests)
    print(f"coverage gaps (not high-confidence): {len(gaps)}")
    for m in gaps:
        print(f"  [{m.confidence}] {m.scenario.name}")
    return 0


def main() -> None:
    global FEATURES_ROOT, TESTS_DIR
    parser = argparse.ArgumentParser(description="Spec MCP server")
    parser.add_argument("--features", type=Path, help="features dir to scope to")
    parser.add_argument("--tests", type=Path, help="tests dir to check coverage against")
    parser.add_argument("--selftest", action="store_true", help="print a summary and exit")
    args = parser.parse_args()

    if args.features:
        FEATURES_ROOT = args.features.resolve()
    if args.tests:
        TESTS_DIR = args.tests.resolve()

    if args.selftest:
        raise SystemExit(_selftest())

    mcp.run()  # stdio transport by default


if __name__ == "__main__":
    main()
