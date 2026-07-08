"""Tests for canonical record types (M01).

Covers construction, version fields, JSON-safe serialization, and to_dict ->
from_dict roundtrip equality (schema compatibility).
"""

import json

import pytest

from src.shared_types import (
    ANALYZER_VERSION,
    POLICY_VERSION,
    SCHEMA_VERSION,
    AudioAsset,
    ConfidenceBand,
    DiagnosticResult,
    EvaluationResult,
    Interpretation,
    Observation,
    ProcessingAction,
    ProcessingObjective,
    ProcessingPlan,
    ProcessingRecord,
    Report,
    band_from_confidence,
    to_serializable,
)


def _full_record() -> ProcessingRecord:
    asset = AudioAsset(
        id="asset-1",
        owner_id="local",
        original_storage_path="in.wav",
        processed_storage_path="out.wav",
        sample_rate=44100,
        channels=1,
        duration=3.0,
        created_at="2026-07-08T00:00:00+00:00",
    )
    diagnostics = DiagnosticResult(
        id="diag-1",
        audio_asset_id=asset.id,
        analyzer_version=ANALYZER_VERSION,
        measurement_context={"quality_score": 62.0, "warnings": ["w1"]},
        observations=(
            Observation(
                id="obs-1",
                metric="harshness",
                value=0.4,
                units="ratio",
                confidence=0.8,
                evidence="severity=SEVERE, peak=3510Hz",
            ),
        ),
        integrity_flags=("clipping",),
    )
    plan = ProcessingPlan(
        id="plan-1",
        preset_profile="adaptive",
        objectives=(ProcessingObjective(id="obj-1", goal="reduce_harshness", priority=1, confidence=0.8),),
        actions=(
            ProcessingAction(
                id="act-1",
                processor="PeakFilter",
                parameters={"freq_hz": 3510, "gain_db": -4, "q": 1.4},
                strength=0.7,
                reason="harshness SEVERE",
                objective_id="obj-1",
            ),
        ),
        skipped_processors=("air_boost",),
        policy_version=POLICY_VERSION,
    )
    evaluation = EvaluationResult(
        id="eval-1",
        before_metrics={"harsh_energy": 100.0},
        after_metrics={"harsh_energy": 60.0},
        deltas={"harsh_energy": -40.0},
        warnings=(),
        passed_checks=("harshness_reduced",),
        failed_checks=(),
    )
    report = Report(
        id="rep-1",
        summary="Reduced harshness while preserving level.",
        findings=("harshness: SEVERE @ 3510Hz",),
        actions=("PeakFilter -4dB @ 3510Hz",),
        limitations=("thresholds uncalibrated",),
        export_path="out.wav",
    )
    return ProcessingRecord(
        id="rec-1",
        asset=asset,
        diagnostics=diagnostics,
        plan=plan,
        evaluation=evaluation,
        report=report,
    )


class TestVersions:
    def test_version_constants_present(self):
        assert SCHEMA_VERSION and ANALYZER_VERSION and POLICY_VERSION

    def test_record_carries_schema_version(self):
        assert _full_record().schema_version == SCHEMA_VERSION

    def test_diagnostic_carries_analyzer_version(self):
        assert _full_record().diagnostics.analyzer_version == ANALYZER_VERSION

    def test_plan_carries_policy_version(self):
        assert _full_record().plan.policy_version == POLICY_VERSION


class TestConfidenceBand:
    @pytest.mark.parametrize(
        "conf,expected",
        [
            (0.9, ConfidenceBand.HIGH),
            (0.66, ConfidenceBand.HIGH),
            (0.5, ConfidenceBand.MEDIUM),
            (0.33, ConfidenceBand.MEDIUM),
            (0.1, ConfidenceBand.LOW),
            (0.0, ConfidenceBand.LOW),
        ],
    )
    def test_band_from_confidence(self, conf, expected):
        assert band_from_confidence(conf) == expected


class TestSerialization:
    def test_to_serializable_is_json_dumpable(self):
        payload = to_serializable(_full_record())
        text = json.dumps(payload)  # must not raise
        assert "harshness" in text
        assert payload["schema_version"] == SCHEMA_VERSION

    def test_record_roundtrip_equal(self):
        rec = _full_record()
        restored = ProcessingRecord.from_dict(rec.to_dict())
        assert restored == rec

    def test_observation_roundtrip_equal(self):
        obs = Observation(id="o", metric="mud", value=0.3, units="ratio", confidence=0.5)
        assert Observation.from_dict(obs.to_dict()) == obs

    def test_interpretation_roundtrip_equal(self):
        interp = Interpretation(
            id="i",
            issue="harshness",
            supporting_observation_ids=("o1", "o2"),
            confidence=0.7,
            rationale="two bands agree",
        )
        assert Interpretation.from_dict(interp.to_dict()) == interp

    def test_plan_roundtrip_preserves_nested_actions(self):
        rec = _full_record()
        restored = ProcessingPlan.from_dict(rec.plan.to_dict())
        assert restored == rec.plan
        assert restored.actions[0].parameters == {"freq_hz": 3510, "gain_db": -4, "q": 1.4}

    def test_empty_record_roundtrip(self):
        rec = ProcessingRecord(id="empty")
        assert ProcessingRecord.from_dict(rec.to_dict()) == rec
