"""Fixture library tests (M02).

Verifies fixtures load deterministically, match their declared metadata, and
that the committed WAV bytes are exactly what the generator produces (drift
guard). Does NOT assert diagnostic severities — that is deferred to M04-M06.
"""

import numpy as np
import pytest

from fixtures import list_fixtures, load_fixture, load_metadata
from fixtures.generate import FIXTURE_SPECS, write_fixtures

EXPECTED_NAMES = {"clean_tone", "harsh", "muddy", "noisy", "clipped", "silence"}


def test_all_fixtures_discovered():
    assert set(list_fixtures()) == EXPECTED_NAMES


@pytest.mark.parametrize("name", sorted(EXPECTED_NAMES))
def test_fixture_loads_and_matches_metadata(name):
    fx = load_fixture(name)
    meta = fx.metadata
    assert fx.audio.ndim == 1
    assert fx.audio.size > 0
    assert np.all(np.isfinite(fx.audio))
    assert fx.sample_rate == meta["sample_rate"] == 44100
    assert meta["channels"] == 1
    duration = fx.audio.size / fx.sample_rate
    assert duration == pytest.approx(meta["duration_seconds"], abs=0.01)


@pytest.mark.parametrize("name", sorted(EXPECTED_NAMES))
def test_metadata_has_required_shape(name):
    meta = load_metadata(name)
    for key in ("name", "category", "description", "sample_rate", "channels",
                "duration_seconds", "audio_path", "expected_diagnoses"):
        assert key in meta, f"{name} missing '{key}'"
    assert meta["name"] == name


def test_load_is_deterministic():
    a = load_fixture("harsh").audio
    b = load_fixture("harsh").audio
    assert np.array_equal(a, b)


def test_committed_bytes_match_generator(tmp_path):
    """Regenerating must reproduce the committed WAV bytes exactly (drift guard)."""
    from fixtures.loader import BASE_DIR

    write_fixtures(tmp_path)
    for name in FIXTURE_SPECS:
        regenerated = (tmp_path / "audio" / f"{name}.wav").read_bytes()
        committed = (BASE_DIR / "audio" / f"{name}.wav").read_bytes()
        assert committed == regenerated, f"{name}.wav drifted from generator"


def test_unknown_fixture_raises():
    with pytest.raises(FileNotFoundError):
        load_fixture("does_not_exist")
