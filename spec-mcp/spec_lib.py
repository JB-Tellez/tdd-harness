"""Parse Gherkin feature files and match scenarios to pytest tests.

This is the *logic* half of the spec MCP, deliberately kept separate from the
server wiring in ``spec_server.py`` so it can be unit-tested without standing
up an MCP server -- and so a student can read the interesting part (how a
scenario gets matched to a test) in one file with no protocol noise.

Two jobs:

1. Parse ``features/**/*.feature`` into structured Scenario objects. We don't
   pull in a full Gherkin library; these specs use a small, regular subset
   (Feature / Scenario / Given-When-Then-And), so a line-oriented parser is
   clearer to read and has no dependency.

2. Decide, heuristically, whether a scenario has a matching test in
   ``tests/``. This is name-matching: we tokenize the scenario title and each
   ``def test_...`` name and score their overlap. It is intentionally fuzzy --
   the honest version of "is this covered?" without wiring specs to tests via
   pytest-bdd. The matcher reports a CONFIDENCE so callers never mistake a
   weak guess for a guarantee.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Gherkin step keywords we recognize. "And"/"But" continue the previous kind,
# but for our purposes we just keep the raw step text.
_STEP_KEYWORDS = ("Given", "When", "Then", "And", "But")

# Words that carry no signal when matching a scenario title to a test name.
# Kept small and visible on purpose -- students should see exactly what we
# throw away, because the stopword list is where a fuzzy matcher quietly lies.
_STOPWORDS = {
    "a", "an", "the", "of", "to", "from", "it", "its", "in", "on", "and",
    "should", "is", "are", "be", "as", "i", "that", "with", "only", "all",
    "them", "their", "not",
    # Every pytest name starts with "test_", so "test" is a constant token
    # across all of them -- pure noise that inflates overlap. Drop it.
    "test",
}


@dataclass
class Scenario:
    feature: str          # Feature name (the "Feature:" line)
    feature_file: str     # Path relative to the features root
    name: str             # Scenario title (the "Scenario:" line)
    steps: list[str] = field(default_factory=list)  # raw "Given ..." lines

    def as_dict(self):
        return {
            "feature": self.feature,
            "feature_file": self.feature_file,
            "name": self.name,
            "steps": list(self.steps),
        }


def parse_feature_file(path: Path, features_root: Path) -> list[Scenario]:
    """Parse one .feature file into a list of Scenario objects."""
    feature_name = ""
    scenarios: list[Scenario] = []
    current: Scenario | None = None
    rel = str(path.relative_to(features_root))

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("Feature:"):
            feature_name = line[len("Feature:"):].strip()
        elif line.startswith("Scenario:"):
            current = Scenario(
                feature=feature_name,
                feature_file=rel,
                name=line[len("Scenario:"):].strip(),
            )
            scenarios.append(current)
        elif current is not None and line.split(" ", 1)[0] in _STEP_KEYWORDS:
            current.steps.append(line)
        # Narrative lines ("As a user...") between Feature: and the first
        # Scenario: are ignored -- they're not steps and not scenarios.
    return scenarios


def load_scenarios(features_root: Path) -> list[Scenario]:
    """Parse every .feature file under ``features_root`` (recursively)."""
    scenarios: list[Scenario] = []
    for path in sorted(features_root.rglob("*.feature")):
        scenarios.extend(parse_feature_file(path, features_root))
    return scenarios


def _tokens(text: str) -> set[str]:
    """Lowercase content words from arbitrary text (title or test name).

    Splits on non-letters, so ``test_deleting_a_todo`` and
    ``"Deleting a todo"`` both reduce to {deleting, todo}.
    """
    words = re.findall(r"[a-z]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def collect_test_names(tests_dir: Path) -> list[str]:
    """Every ``def test_...`` name found under ``tests_dir``."""
    names: list[str] = []
    if not tests_dir.exists():
        return names
    pattern = re.compile(r"^\s*def (test_\w+)", re.MULTILINE)
    for path in sorted(tests_dir.rglob("test_*.py")):
        names.extend(pattern.findall(path.read_text(encoding="utf-8")))
    return names


@dataclass
class Match:
    scenario: Scenario
    test_name: str | None     # best-matching test, or None
    score: float              # Jaccard-ish overlap, 0..1
    confidence: str           # "high" | "low" | "none"

    def as_dict(self):
        return {
            "scenario": self.scenario.name,
            "feature_file": self.scenario.feature_file,
            "test_name": self.test_name,
            "score": round(self.score, 2),
            "confidence": self.confidence,
        }


# Above this overlap we call a scenario "covered" with reasonable confidence.
# Between LOW and HIGH we surface the candidate but flag it as low-confidence,
# so the human (or agent) verifies rather than trusts. Tuned by eye against the
# todo specs; deliberately easy to find and tweak.
_HIGH = 0.5
_LOW = 0.25


def match_scenarios_to_tests(
    scenarios: list[Scenario], test_names: list[str]
) -> list[Match]:
    """Score each scenario against the closest-named test.

    Pure name-matching, no execution. Scoring is token overlap between the
    scenario title and the test name (Jaccard over the smaller set, so a short
    title isn't penalized for a verbose test name). The result is a *guess*
    with a confidence label -- never a coverage guarantee.
    """
    name_tokens = [(n, _tokens(n)) for n in test_names]
    matches: list[Match] = []

    for scenario in scenarios:
        s_tokens = _tokens(scenario.name)
        best_name, best_score = None, 0.0
        for name, t_tokens in name_tokens:
            if not s_tokens or not t_tokens:
                continue
            overlap = len(s_tokens & t_tokens)
            denom = min(len(s_tokens), len(t_tokens))
            score = overlap / denom if denom else 0.0
            if score > best_score:
                best_name, best_score = name, score

        if best_score >= _HIGH:
            confidence = "high"
        elif best_score >= _LOW:
            confidence = "low"
        else:
            confidence = "none"
            best_name = None  # too weak to claim any test at all

        matches.append(Match(scenario, best_name, best_score, confidence))
    return matches


def scenarios_without_tests(
    scenarios: list[Scenario], test_names: list[str]
) -> list[Match]:
    """Matches whose confidence is not "high" -- the coverage gaps.

    Includes "low" confidence ones on purpose: a weak match is a thing to
    *verify*, not to assume covered. The whole point of the tool is to surface
    doubt, not hide it.
    """
    return [
        m
        for m in match_scenarios_to_tests(scenarios, test_names)
        if m.confidence != "high"
    ]
