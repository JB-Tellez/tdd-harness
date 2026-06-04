#!/usr/bin/env python3
"""PreToolUse(Bash) hook: force the canonical pytest invocation.

The skill *asks* the agent to always run `.venv/bin/python -m pytest`, but an
instruction is a suggestion, not a constraint -- and in practice the agent
drifts: bare `python`, `python3`, `PYTHONPATH=src python -m pytest`, wrapped in
`source ...`, etc. Every variant is a different command prefix, so the
allowlist never matches and the user gets a fresh prompt each time.

This hook makes the rule a constraint. If a Bash command invokes pytest in any
form OTHER than the canonical one, it's denied with a message telling the agent
exactly what to run instead. The agent re-issues the canonical form, which the
allowlist covers -- so the prompts stop.

Scope: gated like the other hooks (only acts when the project opted into
tdd-harness), and only touches commands that mention pytest -- everything else
passes through untouched.

Contract: PreToolUse hook. To block, print a JSON deny decision and exit 0.
To allow, exit 0 with no output.
"""

import json
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _testlib import project_dir_from_env, read_tool_input, workflow_enabled  # noqa: E402

CANONICAL = ".venv/bin/python -m pytest"

# The one blessed form: ".venv/bin/python -m pytest" optionally followed by
# flags / -k / node ids. Anchored at the start so nothing is prefixed onto it
# (no PYTHONPATH=, no `source ... &&`).
_CANONICAL_RE = re.compile(r"^\.venv/bin/python -m pytest(\s|$)")

# Does this command invoke pytest at all? (so we leave non-pytest commands be)
_MENTIONS_PYTEST = re.compile(r"(^|\s|/)pytest(\s|$)|-m pytest(\s|$)")


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
    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    project_dir = project_dir_from_env()
    if not workflow_enabled(project_dir):
        sys.exit(0)

    command = (payload.get("tool_input") or {}).get("command", "") or ""

    # Not a pytest command? Not our business.
    if not _MENTIONS_PYTEST.search(command):
        sys.exit(0)

    # Already canonical (and not buried in a compound line)? Allow.
    # We require the command to BE the canonical form, not merely contain it,
    # so `cat x && python -m pytest` (compound) is still corrected.
    if _CANONICAL_RE.match(command.strip()):
        sys.exit(0)

    deny(
        "Non-canonical pytest invocation. This project runs the suite ONE way "
        f"so it stays pre-approved: `{CANONICAL}` (from the project root). "
        "Re-run it exactly that way — to narrow to one test add only `-k` or a "
        "node id (e.g. `" + CANONICAL + " -k completing`). Do NOT use bare "
        "`python`/`python3`, a `PYTHONPATH=` prefix, `source .venv/...`, or a "
        "compound line (`cat ... && ...`). To READ a file, use the Read tool, "
        "not `cat`/`find -exec`."
    )


if __name__ == "__main__":
    main()
