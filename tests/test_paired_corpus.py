"""DT-55B/C — paired-corpus machinery validated on ground-truth surrogates.

Known answers: surrogate wet applies phrase leveling, a -4 dB low-mid cut,
compression, and peak normalization to the same performance the raw derives from.
No gated audio is used anywhere in this suite.
"""
from __future__ import annotations

import numpy as np

from src.paired_corpus import (
    TRUTH,
    align_pair,
    classify_pair,
    global_offset_s,
    make_surrogate_pair,
    profile_pair,
    segment_phrases,
)


# ---------- pairing ----------

def test_same_performance_classifies_as_exact_pair():
    raw, wet, sr, _ = make_surrogate_pair(seed=11)
    ev = classify_pair(raw, wet, sr)
    assert ev.verdict == "verified_exact_pair"
    assert ev.envelope_corr >= 0.6


def test_different_performances_classify_as_incorrect():
    raw, _, sr, _ = make_surrogate_pair(seed=21)
    _, other_wet, _, _ = make_surrogate_pair(seed=99)
    ev = classify_pair(raw, other_wet, sr)
    assert ev.verdict != "verified_exact_pair"


def test_too_short_audio_is_unusable():
    raw = np.zeros(1000, dtype=np.float32)
    wet = np.zeros(1000, dtype=np.float32)
    assert classify_pair(raw, wet, 44100).verdict == "unusable"


# ---------- alignment ----------

def test_known_offset_recovered():
    raw, wet, sr, _ = make_surrogate_pair(seed=31, wet_delay_s=0.8)
    offset, corr = global_offset_s(raw, wet, sr)
    # wet starts 0.8 s LATER; offset convention: shift applied to wet -> -0.8
    assert abs(abs(offset) - 0.8) < 0.05
    assert corr > 0.5


def test_phrase_segmentation_finds_bursts():
    raw, _, sr, _ = make_surrogate_pair(seed=41)
    phrases = segment_phrases(raw, sr)
    assert 3 <= len(phrases) <= 7      # built with 5 bursts


def test_alignment_marks_phrases_aligned_on_true_pair():
    raw, wet, sr, _ = make_surrogate_pair(seed=51)
    amap = align_pair(raw, wet, sr)
    assert len(amap.aligned()) >= 3
    assert all(p.local_corr >= 0.5 for p in amap.aligned())


def test_deleted_phrase_is_not_aligned():
    raw, wet, sr, _ = make_surrogate_pair(seed=61)
    amap0 = align_pair(raw, wet, sr)
    assert len(amap0.aligned()) >= 3
    # silence the wet audio inside the second aligned phrase -> that phrase drops
    victim = amap0.aligned()[1]
    wet_ed = wet.copy()
    wet_ed[int(victim.wet_start_s * sr): int(victim.wet_end_s * sr)] = 0.0
    amap1 = align_pair(raw, wet_ed, sr)
    assert len(amap1.aligned()) < len(amap0.aligned())


# ---------- deltas (known chain signs) ----------

def _summary(seed=71):
    raw, wet, sr, _ = make_surrogate_pair(seed=seed)
    amap = align_pair(raw, wet, sr)
    prof = profile_pair(f"surrogate-{seed}", raw, wet, sr, amap)
    assert prof.n_phrases_aligned >= 3
    return prof.summary


def test_lowmid_cut_detected():
    s = _summary()
    assert s["median_d_lowmid_250_500"] < 0        # wet cut 250-500


def test_compression_reduces_crest():
    s = _summary()
    assert s["median_d_crest_db"] < 0              # wet is compressed


def test_gap_noise_floor_lower_in_wet():
    s = _summary()
    assert s["d_gap_noise_floor_db"] < 0           # wet built from clean; gaps are quiet


def test_phrase_leveling_detected():
    s = _summary()
    assert s["d_phrase_consistency_db"] < 0        # wet phrase RMS spread shrinks


def test_profile_carries_lossy_limitation():
    raw, wet, sr, _ = make_surrogate_pair(seed=81)
    prof = profile_pair("x", raw, wet, sr, align_pair(raw, wet, sr))
    assert "Directional guidance" in prof.limitation
