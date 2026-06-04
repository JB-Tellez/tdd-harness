"""Tests for the canonical-pytest enforcement hook.

Pins the behavior that stops the agent's pytest-invocation drift: anything that
runs pytest in a non-canonical form is denied; the canonical form and
non-pytest commands pass. Run from this folder:
    python -m pytest test_enforce_canonical_pytest.py
"""

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "enforce_canonical_pytest.py"


def _run(command, project_dir):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(project_dir), "PATH": "/usr/bin:/bin"},
    )
    return proc.stdout


def _denies(command, project_dir):
    return '"permissionDecision": "deny"' in _run(command, project_dir)


def _optedin(tmp_path):
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "spec-tdd.json").write_text('{"enforce": true}')
    return tmp_path


# --- drift forms seen in real runs: must be denied -------------------------

def test_bare_python_denied(tmp_path):
    assert _denies("python -m pytest -q", _optedin(tmp_path))


def test_python3_denied(tmp_path):
    assert _denies("python3 -m pytest tests/test_x.py -q", _optedin(tmp_path))


def test_pythonpath_prefix_denied(tmp_path):
    assert _denies("PYTHONPATH=src python -m pytest tests/test_x.py::test_y", _optedin(tmp_path))


def test_compound_line_denied(tmp_path):
    assert _denies("cat src/x.py && python -m pytest", _optedin(tmp_path))


# --- canonical + non-pytest: must pass -------------------------------------

def test_canonical_allowed(tmp_path):
    assert not _denies(".venv/bin/python -m pytest", _optedin(tmp_path))


def test_canonical_with_filter_allowed(tmp_path):
    assert not _denies(".venv/bin/python -m pytest -k completing", _optedin(tmp_path))


def test_non_pytest_command_ignored(tmp_path):
    assert not _denies("git status --short", _optedin(tmp_path))


# --- gating: inert when the project hasn't opted in ------------------------

def test_inert_when_not_opted_in(tmp_path):
    (tmp_path / ".claude").mkdir()  # no spec-tdd.json
    assert not _denies("python -m pytest -q", tmp_path)
