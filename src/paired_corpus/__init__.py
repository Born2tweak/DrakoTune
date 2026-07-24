"""Paired raw/wet corpus machinery (DT-55B/C).

Pair verification, phrase alignment, and raw→wet delta profiling — validated on
manufactured ground-truth surrogates (`surrogates.py`) so no gated audio is needed
for tests. Real-corpus execution is authorized by D-029 (local, internal,
evaluation-only; leaked/AI-isolated rejected; nothing redistributed or claimed).
"""
from src.paired_corpus.alignment import (
    AlignmentMap,
    PhraseMatch,
    align_pair,
    envelope,
    global_offset_s,
    segment_phrases,
)
from src.paired_corpus.deltas import (
    PhraseDelta,
    TransformProfile,
    phrase_features,
    profile_pair,
)
from src.paired_corpus.pairing import PairEvidence, classify_pair
from src.paired_corpus.surrogates import (
    TRUTH,
    degrade_to_raw,
    make_performance,
    make_surrogate_pair,
    pro_chain_to_wet,
)

__all__ = [
    "AlignmentMap", "PhraseMatch", "align_pair", "envelope", "global_offset_s",
    "segment_phrases",
    "PhraseDelta", "TransformProfile", "phrase_features", "profile_pair",
    "PairEvidence", "classify_pair",
    "TRUTH", "degrade_to_raw", "make_performance", "make_surrogate_pair",
    "pro_chain_to_wet",
]
