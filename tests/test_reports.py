"""Report engine tests (M11).

Verifies the report includes findings/confidence/actions/skipped/evaluation/
limitations, uses confidence bands (no fake precision), and is deterministic.
"""

import numpy as np

from fixtures.loader import AUDIO_DIR, load_fixture
from src.dsp_engine import execute_plan
from src.evaluation import evaluate_arrays
from src.orchestration import analyze_and_plan
from src.reports import build_report, render_markdown

SR = 44100


def _bundle_eval(name: str):
    src = AUDIO_DIR / f"{name}.wav"
    bundle = analyze_and_plan(str(src))
    before = load_fixture(name).audio
    after, _ = execute_plan(before, SR, bundle.plan)
    after = after[:, 0] if after.ndim > 1 else after
    evaluation = evaluate_arrays(before, after, SR, plan=bundle.plan, eval_id=name)
    return bundle, evaluation


class TestContent:
    def test_report_has_all_sections(self):
        bundle, evaluation = _bundle_eval("harsh")
        md = render_markdown(build_report(bundle, evaluation, "harsh"), evaluation)
        # Report engine 2.0.0 (M27): "Evaluation" became "What changed".
        for section in ("## Findings", "## Actions", "## What changed", "## Limitations"):
            assert section in md

    def test_findings_use_confidence_bands_not_percentages(self):
        bundle, evaluation = _bundle_eval("harsh")
        report = build_report(bundle, evaluation, "harsh")
        conf_findings = [f for f in report.findings if "confidence" in f]
        assert conf_findings
        for f in conf_findings:
            assert any(band in f for band in ("high", "medium", "low"))
            assert "%" not in f  # no fake precision on confidence

    def test_actions_include_applied_and_skipped(self):
        # Analyzer 1.2.0: the harsh fixture no longer produces a natural skip,
        # so the skip-rendering contract is pinned with an explicit skip entry.
        import dataclasses

        bundle, evaluation = _bundle_eval("harsh")
        plan_with_skip = dataclasses.replace(
            bundle.plan,
            skipped_processors=bundle.plan.skipped_processors
            + ("PeakFilter:sibilance (report-only: low confidence)",),
        )
        bundle = dataclasses.replace(bundle, plan=plan_with_skip)
        report = build_report(bundle, evaluation, "harsh")
        assert any(a.startswith("applied ") for a in report.actions)
        assert any(a.startswith("skipped ") for a in report.actions)

    def test_limitations_present(self):
        bundle, evaluation = _bundle_eval("harsh")
        report = build_report(bundle, evaluation, "harsh")
        assert report.limitations
        assert any("not a professional" in limitation.lower() for limitation in report.limitations)

    def test_evaluation_deltas_rendered(self):
        bundle, evaluation = _bundle_eval("harsh")
        md = render_markdown(build_report(bundle, evaluation, "harsh"), evaluation)
        assert "loudness change:" in md


class TestBlockedInput:
    def test_clipped_report_notes_enhancement_blocked(self):
        bundle, evaluation = _bundle_eval("clipped")
        report = build_report(bundle, evaluation, "clipped")
        assert "blocked" in report.summary.lower()


class TestDeterminism:
    def test_report_deterministic(self):
        bundle, evaluation = _bundle_eval("harsh")
        a = render_markdown(build_report(bundle, evaluation, "harsh"), evaluation)
        b = render_markdown(build_report(bundle, evaluation, "harsh"), evaluation)
        assert a == b

    def test_report_has_stable_id(self):
        bundle, evaluation = _bundle_eval("muddy")
        assert build_report(bundle, evaluation, "muddy").id == "report:muddy"


class TestReportV2:
    def test_manifest_is_machine_readable_and_versioned(self):
        import json

        from src.reports import build_manifest

        bundle, evaluation = _bundle_eval("harsh")
        report = build_report(bundle, evaluation, "harsh")
        manifest = build_manifest(bundle, evaluation, report)
        json.dumps(manifest)  # must be serializable
        assert manifest["report_engine_version"] == "2.0.0"
        assert manifest["analyzers"]["spectral"].startswith("1.2")
        assert manifest["plan"]["actions"] or manifest["plan"]["skipped"] is not None

    def test_advisory_issues_surface_as_cannot_fix_guidance(self):
        from src.shared_types import Interpretation

        bundle, evaluation = _bundle_eval("harsh")
        advisory = (Interpretation(
            id="interp.hum", issue="hum", supporting_observation_ids=(),
            confidence=0.8, rationale="test"),)
        report = build_report(bundle, evaluation, "harsh",
                              advisory_interpretations=advisory)
        assert any("advisory hum" in f for f in report.findings)
        assert any(lim.startswith("cannot fix — hum") for lim in report.limitations)
        md = render_markdown(report, evaluation)
        assert "cannot fix" in md.lower() and "rerecord" in md.lower()
