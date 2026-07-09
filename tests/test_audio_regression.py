"""Audio regression tests (M15).

Runs the decision-fingerprint check inside the normal suite so drift in what
DrakoTune decides is caught locally and in CI. Fingerprints are decision-level
(objectives, applied processors, skipped issues, safety decision, pass/fail) and
exclude raw floats, so they are stable but sensitive to logic changes.
"""

import json

import pytest

from fixtures import list_fixtures
from scripts.audio_regression import build_fingerprint, golden_path


@pytest.mark.parametrize("name", sorted(list_fixtures()))
def test_fixture_fingerprint_matches_golden(name):
    gp = golden_path(name)
    assert gp.exists(), f"missing golden for {name} (run: python scripts/audio_regression.py --update)"
    expected = json.loads(gp.read_text())
    actual = build_fingerprint(name)
    assert actual == expected, (
        f"decision fingerprint changed for {name}; if intended, run "
        f"`python scripts/audio_regression.py --update` and review the diff."
    )


@pytest.mark.parametrize("name", sorted(list_fixtures()))
def test_fingerprint_is_deterministic(name):
    assert build_fingerprint(name) == build_fingerprint(name)


def test_mutation_is_detected():
    """Sanity: a changed fingerprint must not equal its golden."""
    name = "harsh"
    golden = json.loads(golden_path(name).read_text())
    mutated = dict(golden)
    mutated["objectives"] = golden["objectives"] + ["reduce_rumble"]
    assert mutated != golden
