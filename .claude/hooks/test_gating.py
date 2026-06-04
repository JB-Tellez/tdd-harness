"""Tests for the hook gate -- the check that keeps these hooks INERT in repos
that didn't opt into tdd-harness.

This is the safety property that matters most once the hooks ship as a global
plugin: firing in an unrelated repo and blocking its edits would make that repo
feel broken. These tests pin "off by default, on only with explicit opt-in".

Run from this folder:  python -m pytest test_gating.py
"""

import json

import _testlib


def _project(tmp_path, config=None):
    """A temp project root, optionally with .claude/tdd-harness.json written."""
    claude = tmp_path / ".claude"
    claude.mkdir()
    if config is not None:
        (claude / "tdd-harness.json").write_text(json.dumps(config))
    return str(tmp_path)


def test_disabled_when_no_config_file(tmp_path):
    # The unrelated-repo case: no opt-in file at all -> hooks stay inert.
    assert _testlib.workflow_enabled(_project(tmp_path)) is False


def test_enabled_with_enforce_true(tmp_path):
    assert _testlib.workflow_enabled(_project(tmp_path, {"enforce": True})) is True


def test_disabled_with_enforce_false(tmp_path):
    assert _testlib.workflow_enabled(_project(tmp_path, {"enforce": False})) is False


def test_disabled_when_enforce_key_missing(tmp_path):
    # A config file with no "enforce" key defaults to OFF (fail safe).
    assert _testlib.workflow_enabled(_project(tmp_path, {"other": 1})) is False


def test_disabled_on_malformed_config(tmp_path):
    # Unreadable/invalid JSON must not throw and must not enable -- erring
    # toward OFF, because wrongly blocking edits is the bad failure.
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "tdd-harness.json").write_text("{ not valid json")
    assert _testlib.workflow_enabled(str(tmp_path)) is False
