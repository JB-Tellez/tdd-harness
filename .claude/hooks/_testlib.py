"""Shared helpers for the auto-tdd teaching hooks.

Both hooks need the same two things: figure out whether a tool call is about
to touch production code (anything under ``src/``), and run the test suite to
learn the current red/green state. Keeping that logic here means the two hook
scripts stay short enough to read in one sitting -- which matters, because for
this class the hooks are teaching artifacts as much as they are enforcement.
"""

import json
import os
import subprocess
import sys


def read_tool_input():
    """Parse the hook payload Claude Code sends on stdin.

    The payload is a JSON object; the fields we care about are ``tool_name``
    and ``tool_input`` (which holds ``file_path`` for Edit/Write). Returns the
    whole dict so a hook can inspect whatever it needs.
    """
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def edited_path(payload):
    """The file path an Edit/Write tool call targets, or '' if none."""
    return (payload.get("tool_input") or {}).get("file_path", "") or ""


def is_production_code(path, project_dir):
    """True if ``path`` is a source file under the project's ``src/`` dir.

    Test files live under ``tests/`` (see pytest.ini), so they're explicitly
    NOT production code -- the whole point is that writing a *test* is always
    allowed; only writing *implementation* is gated.
    """
    if not path:
        return False
    abs_path = os.path.abspath(path)
    src_dir = os.path.abspath(os.path.join(project_dir, "src"))
    return abs_path.startswith(src_dir + os.sep) and abs_path.endswith(".py")


def python_for(project_dir):
    """Pick an interpreter to run pytest with.

    Prefer the project's local ``.venv`` (the AGENTS.md workflow), but fall
    back to the interpreter running this hook so the demo still works before
    anyone has created a venv.
    """
    venv_py = os.path.join(project_dir, ".venv", "bin", "python")
    return venv_py if os.path.exists(venv_py) else sys.executable


def run_pytest(project_dir):
    """Run the suite quietly and return (state, output).

    ``state`` is one of: "green", "red", "none", "error". We classify here --
    rather than leaking raw exit codes -- because pytest's exit 1 is ambiguous:
    it means "a test failed" but ALSO surfaces when pytest can't even start
    (e.g. it isn't installed). A hook must not mistake "pytest is broken" for
    "a test is red," or the gate silently stops gating. So:

      green : exit 0                      -- all tests passed
      red   : exit 1 AND a real summary   -- at least one test genuinely failed
      none  : exit 5                      -- no tests collected
      error : anything else, or exit 1    -- pytest did not actually run a suite
              with no test-result summary    (missing pytest, import/collection
                                              failure, internal error)

    Run from the project root so pytest.ini (pythonpath=src, testpaths=tests)
    applies.
    """
    try:
        proc = subprocess.run(
            [python_for(project_dir), "-m", "pytest", "-q"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return "error", f"could not launch pytest: {exc}"

    output = (proc.stdout or "") + (proc.stderr or "")
    code = proc.returncode

    if code == 0:
        return "green", output
    if code == 5:
        return "none", output
    if code == 1 and _has_result_summary(output):
        return "red", output
    return "error", output


def _has_result_summary(output):
    """True if pytest printed a real pass/fail tally (proof a suite ran).

    "No module named pytest" or a collection error exits 1 with no such line,
    which is how we tell a broken run apart from a genuinely failing test.
    """
    markers = (" passed", " failed", " error", " skipped", " xfailed", " deselected")
    return any(m in line for line in output.splitlines() for m in markers)


def project_dir_from_env():
    """The directory Claude Code is operating in for this session."""
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


# Opt-in config file the tdd-harness workflow owns, in the *project's* .claude/.
# Kept separate from Claude Code's own settings.json so we never collide with
# its schema; it's purely our gate signal.
_CONFIG_NAME = "tdd-harness.json"


def workflow_enabled(project_dir):
    """True only if the current project has opted into tdd-harness enforcement.

    This is the gate that keeps the hooks INERT in unrelated repos. As a
    globally-enabled plugin, these hooks fire on every Edit/Write in every
    project; without this check, a non-pytest repo would get its src/ edits
    blocked (fail-closed) for no reason. We require an explicit opt-in:

        .claude/tdd-harness.json  ->  {"enforce": true}

    Absent file, missing/false "enforce", or unreadable config -> disabled.
    Erring toward OFF is deliberate: a hook that wrongly stays silent is a
    non-event; a hook that wrongly blocks edits makes a stranger's repo feel
    broken.
    """
    config_path = os.path.join(project_dir, ".claude", _CONFIG_NAME)
    try:
        with open(config_path, encoding="utf-8") as fh:
            return bool(json.load(fh).get("enforce", False))
    except (OSError, ValueError):
        return False
