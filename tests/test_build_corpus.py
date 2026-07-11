"""Corpus builder tests (M22, part 2).

CI-safe: tests that need the locally downloaded datasets (data/local/) skip
when they are absent; committed artifacts (CI fixtures, corpus freeze summary)
are always verified.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from build_corpus import (  # noqa: E402
    CLEAN_TARGET_LUFS,
    SR,
    _load_normalized,
    assign_recipes,
    select_vocadito_clips,
    select_vocalset_clips,
)
from fixtures.degradations import STANDARD_GRID  # noqa: E402

FIXTURE_DIR = REPO / "fixtures" / "audio_real"
FREEZE = REPO / "data" / "corpus" / "corpus-v1.json"
VOCALSET_LOCAL = REPO / "data" / "local" / "vocalset"
VOCADITO_LOCAL = REPO / "data" / "local" / "vocadito"

needs_local_data = pytest.mark.skipif(
    not (VOCALSET_LOCAL.exists() and VOCADITO_LOCAL.exists()),
    reason="Tier A datasets not downloaded on this machine (governance §4)",
)


# --- always-run: committed artifacts ----------------------------------------

def test_ci_fixtures_are_valid_and_small():
    wavs = sorted(FIXTURE_DIR.glob("*.wav"))
    assert len(wavs) == 3, "expected 3 real-vocal CI fixtures"
    for wav in wavs:
        assert wav.stat().st_size <= 1_000_000, f"{wav.name} exceeds 1 MB"
        info = sf.info(wav)
        assert info.samplerate == SR and info.channels == 1
        assert info.subtype == "PCM_16"
        assert info.frames / info.samplerate <= 10.5
    assert (FIXTURE_DIR / "README.md").exists(), "attribution README required"


def test_corpus_freeze_summary():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert freeze["corpus_version"] == "corpus-v1"
    assert freeze["clip_count"] == len(freeze["clip_digests"]) > 0
    assert freeze["degraded_pair_count"] >= freeze["clip_count"]
    assert set(freeze["sources"]) == {"vocalset", "vocadito"}
    for digest in freeze["clip_digests"].values():
        assert len(digest) == 64


# --- always-run: pure functions ----------------------------------------------

def test_assign_recipes_deterministic_and_covering():
    clip_ids = [f"clip_{i:03d}" for i in range(60)]
    a = assign_recipes(clip_ids, full_grid=False)
    b = assign_recipes(clip_ids, full_grid=False)
    assert {k: [r.id for r in v] for k, v in a.items()} == \
           {k: [r.id for r in v] for k, v in b.items()}
    used = {r.id for recipes in a.values() for r in recipes}
    assert used == {r.id for r in STANDARD_GRID}, "round-robin must cover every recipe"
    full = assign_recipes(clip_ids[:2], full_grid=True)
    assert all(len(v) == len(STANDARD_GRID) for v in full.values())


def test_load_normalized_hits_target_loudness(tmp_path):
    import pyloudnorm
    t = np.arange(SR * 5) / SR
    tone = (0.05 * np.sin(2 * np.pi * 220 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 2 * t))).astype(np.float32)
    src = tmp_path / "tone.wav"
    sf.write(src, tone, SR)
    audio = _load_normalized(src)
    assert audio is not None
    lufs = pyloudnorm.Meter(SR).integrated_loudness(audio.astype(np.float64))
    assert abs(lufs - CLEAN_TARGET_LUFS) < 1.0
    assert np.max(np.abs(audio)) <= 0.85


def test_load_normalized_rejects_short_audio(tmp_path):
    src = tmp_path / "short.wav"
    sf.write(src, np.zeros(SR, dtype=np.float32), SR)  # 1 s < CLIP_MIN_S
    assert _load_normalized(src) is None


# --- local-data-only: selection determinism -----------------------------------

@needs_local_data
def test_vocalset_selection_deterministic_and_diverse():
    first = select_vocalset_clips(VOCALSET_LOCAL)
    second = select_vocalset_clips(VOCALSET_LOCAL)
    assert first == second
    singers = {c["singer"] for c in first}
    assert len(singers) == 20, "expected all 20 VocalSet singers represented"
    assert len({c["clip_id"] for c in first}) == len(first)


@needs_local_data
def test_vocadito_selection_complete():
    clips = select_vocadito_clips(VOCADITO_LOCAL)
    assert len(clips) == 40
    assert clips == select_vocadito_clips(VOCADITO_LOCAL)
