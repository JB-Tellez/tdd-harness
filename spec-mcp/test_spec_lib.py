"""Tests for the spec-MCP logic (parser + heuristic matcher).

Self-contained: each test writes its own tiny .feature / test files into a
temp dir, so the suite passes in a freshly-copied template with no dependence
on any particular project specs. They pin the behavior the MCP tools rely on
and double as documentation of the matcher's *known* limits -- including the
within-feature mis-pointer, asserted on purpose so nobody "fixes" it by
accident. Run from this folder:  python -m pytest test_spec_lib.py
"""

import spec_lib

_FEATURE = """\
Feature: Manage widgets

  As a user
  I want to manage widgets

  Scenario: Adding a widget captures its name
    Given a new widget named "spinner"
    When I inspect the widget
    Then its name should be "spinner"

  Scenario: Listing widgets returns all of them
    Given I have added widgets "spinner" and "gear"
    When I list the widgets
    Then I should see both "spinner" and "gear"
"""

_TESTS = '''\
def test_adding_a_widget_captures_its_name():
    pass


def test_listing_widgets_returns_all_of_them():
    pass
'''


def _write(tmp_path, feature=_FEATURE, tests=_TESTS):
    features_dir = tmp_path / "features"
    tests_dir = tmp_path / "tests"
    features_dir.mkdir()
    tests_dir.mkdir()
    (features_dir / "widgets.feature").write_text(feature)
    if tests is not None:
        (tests_dir / "test_widgets.py").write_text(tests)
    return features_dir, tests_dir


def test_parses_scenarios_and_steps(tmp_path):
    features_dir, _ = _write(tmp_path)
    scenarios = spec_lib.load_scenarios(features_dir)
    assert len(scenarios) == 2
    # Steps are captured; the narrative ("As a user...") is not.
    adding = next(s for s in scenarios if s.name.startswith("Adding"))
    assert adding.steps[0].startswith("Given a new widget")
    assert all(
        step.split(" ", 1)[0] in ("Given", "When", "Then", "And", "But")
        for step in adding.steps
    )


def test_matching_tests_means_no_gaps(tmp_path):
    # Scenario names and test names share tokens -> high-confidence cover.
    features_dir, tests_dir = _write(tmp_path)
    scenarios = spec_lib.load_scenarios(features_dir)
    tests = spec_lib.collect_test_names(tests_dir)
    assert spec_lib.scenarios_without_tests(scenarios, tests) == []


def test_no_tests_means_every_scenario_is_a_gap(tmp_path):
    # The keystone guarantee: with no tests, nothing is falsely "covered".
    features_dir, tests_dir = _write(tmp_path, tests=None)
    scenarios = spec_lib.load_scenarios(features_dir)
    tests = spec_lib.collect_test_names(tests_dir)
    gaps = spec_lib.scenarios_without_tests(scenarios, tests)
    assert len(gaps) == len(scenarios)
    assert all(m.confidence == "none" for m in gaps)


def test_tokenizer_drops_stopwords_and_test_prefix(tmp_path):
    assert spec_lib._tokens("Adding a widget to the list") == {"adding", "widget", "list"}
    # "test" is dropped because every pytest name carries it -- pure noise.
    assert spec_lib._tokens("test_adding_a_widget") == {"adding", "widget"}
