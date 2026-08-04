"""V3 product-route integration tests (DT-96/97).

DT-94/95 were reachable only through standalone scripts. These tests pin the two
routes that actually matter, so "the engine supports it" can never again drift
apart from "the product does it":

    application/CLI request -> V3 graph -> exported audio
    browser upload          -> mode selection -> processing -> A/B -> export

They also pin the guarantee that makes V3 safe to ship: a V2 request is
unaffected by any of it.
"""

import pathlib

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from src.application.service import ApplicationService
from src.dsp.preprocess import preprocess
from src.modes import EXPERIMENTAL_MODES, list_modes
from src.dsp_engine.channels import mono_compatibility
from src.dsp_engine.executor import execute_plan, render_mode
from src.dsp_engine.gain_staging import (
    EXPORT_TARGET_PEAK_DBFS,
    GainStage,
    stage_output,
)
from src.evaluation.semantics.enums import ResultStatus
from src.orchestration import analyze_and_plan
from src.webapp.app import app
from src.webapp.jobs import UnknownModeError, process_upload

FIXTURE = "fixtures/audio/muddy.wav"
SR = 44100


def _rms(a):
    return float(np.sqrt(np.mean(np.square(a, dtype=np.float64)))) if a.size else 0.0


# -- Route 1: application service / CLI --------------------------------------
class TestApplicationRoute:
    def test_service_renders_a_mode_to_a_file(self, tmp_path):
        out = tmp_path / "out.wav"
        result = ApplicationService().render_mode(FIXTURE, str(out), "rescue", "bold")
        assert result.status is ResultStatus.PASSED
        assert out.exists() and out.stat().st_size > 0
        audio, _ = sf.read(str(out), dtype="float32")
        assert np.all(np.isfinite(audio))

    def test_service_reports_build_identity(self, tmp_path):
        result = ApplicationService().render_mode(
            FIXTURE, str(tmp_path / "o.wav"), "modern_rap")
        assert result.build.engine_version

    def test_unknown_mode_is_a_typed_error_not_a_crash(self, tmp_path):
        result = ApplicationService().render_mode(FIXTURE, str(tmp_path / "o.wav"), "nope")
        assert result.status is ResultStatus.ERROR
        assert any("unknown_mode" in r for r in result.reasons)
        assert not (tmp_path / "o.wav").exists(), "no file on a failed render"

    def test_cancellation_writes_no_file(self, tmp_path):
        out = tmp_path / "o.wav"
        result = ApplicationService().render_mode(
            FIXTURE, str(out), "rescue", cancel=lambda: True)
        assert result.status is ResultStatus.CANCELLED
        assert not out.exists()

    def test_orchestration_carries_the_mode_selection(self):
        bundle = analyze_and_plan(FIXTURE, mode="rescue", intensity="bold")
        assert bundle.is_v3 and bundle.mode == "rescue" and bundle.intensity == "bold"

    def test_diagnosis_runs_identically_with_and_without_a_mode(self):
        """A mode changes what is applied, never what was observed."""
        v2 = analyze_and_plan(FIXTURE)
        v3 = analyze_and_plan(FIXTURE, mode="modern_rap", intensity="bold")
        assert not v2.is_v3 and v3.is_v3
        assert [o.goal for o in v2.plan.objectives] == [o.goal for o in v3.plan.objectives]

    def test_unknown_mode_rejected_at_plan_time(self):
        with pytest.raises(KeyError):
            analyze_and_plan(FIXTURE, mode="not_a_mode")

    def test_render_mode_writes_all_three_modes(self, tmp_path):
        for mode in ("natural", "rescue", "modern_rap"):
            out = tmp_path / f"{mode}.wav"
            render_mode(FIXTURE, str(out), mode, "bold")
            assert out.exists()


# -- Route 2: browser upload -------------------------------------------------
class TestWebRoute:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_modes_endpoint_lists_modes_and_intensities(self, client):
        body = client.get("/api/modes").json()
        names = [m["name"] for m in body["modes"]]
        assert {"natural", "rescue", "modern_rap"} <= set(names)
        assert body["intensities"] == ["subtle", "balanced", "bold", "extreme"]

    def test_modes_endpoint_exposes_honest_capabilities(self, client):
        """The client renders these verbatim, so they must not overclaim."""
        body = client.get("/api/modes").json()
        blob = " ".join(
            c.lower() for m in body["modes"] for c in m["capabilities"]
        )
        assert "auto-tune" not in blob and "pitch correction" not in blob
        assert "plate" not in blob
        # Denoising may only appear as an explicit disclaimer.
        assert "denoising" not in blob.replace("not broadband denoising", "")

    def test_upload_with_mode_selection_completes(self, client):
        with open(FIXTURE, "rb") as fh:
            resp = client.post(
                "/api/audio/upload",
                files={"file": ("vocal.wav", fh, "audio/wav")},
                data={"mode": "rescue", "intensity": "bold"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["mode"] == "rescue" and body["intensity"] == "bold"

    def test_upload_without_mode_still_uses_v2(self, client):
        with open(FIXTURE, "rb") as fh:
            resp = client.post("/api/audio/upload",
                               files={"file": ("vocal.wav", fh, "audio/wav")})
        assert resp.json()["mode"] is None

    def test_job_produces_a_loudness_matched_ab_pair(self):
        """The A/B transport needs a fair pair, not the raw export levels."""
        job = process_upload("v.wav", open(FIXTURE, "rb").read(),
                             mode="modern_rap", intensity="bold")
        assert job.status == "completed"
        assert job.previews_matched, "no matched pair produced for audition"
        a, _ = sf.read(str(job.before_preview_path), dtype="float32")
        b, _ = sf.read(str(job.after_preview_path), dtype="float32")
        assert _rms(a) == pytest.approx(_rms(b), rel=0.35)

    def test_explicit_invalid_mode_is_refused_never_substituted(self):
        """DT-97 corrective: a typo must not silently render a different chain.

        The original behaviour coerced an unknown mode to None and rendered V2,
        so a user who asked for "modrn_rap" received the V2 clean chain and a
        job reporting mode=null. Asking for something that does not exist is now
        an error carrying the list of things that do.
        """
        with pytest.raises(UnknownModeError) as excinfo:
            process_upload("v.wav", open(FIXTURE, "rb").read(), mode="modrn_rap")
        assert excinfo.value.requested == "modrn_rap"
        assert "modern_rap" in excinfo.value.available

    def test_omitting_mode_is_still_a_valid_v2_request(self):
        """Only an *explicit* unknown value is refused; absence is not an error."""
        job = process_upload("v.wav", open(FIXTURE, "rb").read())
        assert job.status == "completed"
        assert job.mode is None

    def test_job_reports_what_the_gain_stage_did(self):
        """F-12 follow-up: the makeup applied is a fact, not something to infer."""
        job = process_upload("v.wav", open(FIXTURE, "rb").read(),
                             mode="rescue", intensity="bold")
        assert job.gain_staging is not None
        assert job.gain_staging["stage"] == "export"
        assert "applied_db" in job.gain_staging
        assert "makeup_clamped" in job.gain_staging

    def test_job_reports_delivered_file_measurements(self):
        """Descriptive telemetry about the file the user keeps."""
        job = process_upload("v.wav", open(FIXTURE, "rb").read(),
                             mode="modern_rap", intensity="bold")
        d = job.delivery
        assert d is not None
        for key in ("sample_peak_dbfs", "true_peak_dbfs", "integrated_lufs",
                    "crest_factor_db", "clipped_samples", "channels"):
            assert key in d, f"missing delivery metric: {key}"

    def test_delivery_metrics_are_not_a_quality_verdict(self):
        """The payload must stay descriptive; a score here would be a claim."""
        job = process_upload("v.wav", open(FIXTURE, "rb").read(), mode="natural")
        forbidden = ("score", "quality", "grade", "rating", "verdict")
        assert not [k for k in job.delivery if any(f in k.lower() for f in forbidden)]

    def test_modes_endpoint_distinguishes_modes_from_intensities(self, client):
        body = client.get("/api/modes").json()
        # 3 production chains + 3 DT-108 experimental challengers. The point of
        # this test is that intensities are not counted as modes, not the total.
        assert body["counts"]["modes"] == len(list_modes())
        assert body["counts"]["intensities_per_mode"] == 4

    def test_modes_endpoint_marks_experimental_chains(self, client):
        """A challenger must be visibly experimental wherever it is offered, so a
        user cannot mistake an unvalidated reconstruction for a shipped chain."""
        body = client.get("/api/modes").json()
        by_name = {m["name"]: m for m in body["modes"]}
        for name in EXPERIMENTAL_MODES:
            assert name in by_name, f"{name} missing from /api/modes"
            assert "experimental" in by_name[name]["title"].lower()

    def test_api_rejects_an_unknown_mode_with_the_available_list(self, client):
        with open(FIXTURE, "rb") as fh:
            resp = client.post("/api/audio/upload",
                               files={"file": ("vocal.wav", fh, "audio/wav")},
                               data={"mode": "modrn_rap"})
        assert resp.status_code == 400
        body = resp.json()
        assert body["error"] == "unknown_mode"
        assert body["requested"] == "modrn_rap"
        assert "modern_rap" in body["available_modes"]


# -- Gain staging ------------------------------------------------------------
class TestGainStaging:
    def test_export_reaches_the_target_level(self):
        """A chain that cut a few dB gets made up to the intended export level.

        0.3 peak needs ~9.5 dB, inside the makeup budget — this is the realistic
        case, matching the 3.7-8.3 dB drops the DT-95 mode renders showed.
        """
        cut = (np.sin(2 * np.pi * 300 * np.arange(SR) / SR) * 0.3).astype(np.float32)
        out, info = stage_output(cut, GainStage.EXPORT)
        assert info.applied_db > 0
        assert not info.makeup_clamped
        assert float(np.max(np.abs(out))) == pytest.approx(
            10 ** (EXPORT_TARGET_PEAK_DBFS / 20), rel=0.05)

    def test_export_attenuates_a_hot_signal_in_full(self):
        """Only boosting is capped; a too-loud file is always brought down."""
        hot = (np.sin(2 * np.pi * 300 * np.arange(SR) / SR) * 0.99).astype(np.float32)
        out, info = stage_output(hot, GainStage.EXPORT)
        assert info.applied_db < 0
        assert float(np.max(np.abs(out))) == pytest.approx(
            10 ** (EXPORT_TARGET_PEAK_DBFS / 20), rel=0.05)

    def test_raw_never_changes_level(self):
        quiet = (np.sin(2 * np.pi * 300 * np.arange(SR) / SR) * 0.02).astype(np.float32)
        out, info = stage_output(quiet, GainStage.RAW)
        assert info.applied_db == 0.0
        assert float(np.max(np.abs(out))) == pytest.approx(0.02, rel=1e-3)

    def test_makeup_is_capped_so_near_silence_is_not_amplified(self):
        near_silence = (np.sin(2 * np.pi * 300 * np.arange(SR) / SR) * 1e-5).astype(np.float32)
        _, info = stage_output(near_silence, GainStage.EXPORT)
        assert info.makeup_clamped

    def test_ceiling_is_never_exceeded_in_any_stage(self):
        hot = (np.sin(2 * np.pi * 300 * np.arange(SR) / SR) * 0.99).astype(np.float32)
        for stage in GainStage:
            out, _ = stage_output(hot, stage)
            assert float(np.max(np.abs(out))) <= 10 ** (-0.2 / 20) + 1e-6

    def test_export_render_is_not_quieter_than_the_source(self):
        """The defect this fixes: correct chains handing back quiet files."""
        import tempfile, pathlib
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td) / "o.wav"
            render_mode(FIXTURE, str(out), "modern_rap", "bold", stage=GainStage.EXPORT)
            src, _ = sf.read(FIXTURE, dtype="float32")
            dst, _ = sf.read(str(out), dtype="float32")
            assert float(np.max(np.abs(dst))) > float(np.max(np.abs(src))) * 0.7


# -- Stereo path -------------------------------------------------------------
class TestStereoPath:
    def test_preprocess_can_emit_stereo(self, tmp_path):
        out = tmp_path / "s.wav"
        preprocess(FIXTURE, out, channels=2)
        assert sf.info(str(out)).channels == 2

    def test_preprocess_defaults_to_mono_for_vocal_input(self, tmp_path):
        out = tmp_path / "m.wav"
        preprocess(FIXTURE, out)
        assert sf.info(str(out)).channels == 1

    def test_preprocess_rejects_unsupported_channel_counts(self, tmp_path):
        with pytest.raises(ValueError):
            preprocess(FIXTURE, tmp_path / "x.wav", channels=6)

    def test_stereo_survives_preprocess_graph_and_export(self, tmp_path):
        """The full path the mono-by-accident defect used to break."""
        stereo_in = tmp_path / "in.wav"
        preprocess(FIXTURE, stereo_in, channels=2)
        out = tmp_path / "out.wav"
        render_mode(str(stereo_in), str(out), "modern_rap", "extreme")
        assert sf.info(str(out)).channels == 2

    def test_exported_stereo_is_mono_compatible(self, tmp_path):
        stereo_in = tmp_path / "in.wav"
        preprocess(FIXTURE, stereo_in, channels=2)
        out = tmp_path / "out.wav"
        render_mode(str(stereo_in), str(out), "modern_rap", "extreme")
        audio, _ = sf.read(str(out), dtype="float32")
        assert not mono_compatibility(audio).collapses


# -- V2 preservation ---------------------------------------------------------
def test_v2_flat_path_is_untouched_by_v3():
    """The whole V3 track must be invisible to a request that does not use it."""
    bundle = analyze_and_plan(FIXTURE)
    audio, sr = sf.read(FIXTURE, dtype="float32")
    processed, result = execute_plan(audio, int(sr), bundle.plan)
    assert np.all(np.isfinite(processed))
    assert "graph" not in result.chain_description()


class TestOversizedInputIsRefusedNotFatal:
    """Regression for the 2026-08-04 production OOM.

    A full-length vocal killed the container mid-render. Because the job store is
    in memory, the reboot destroyed the in-flight job and the browser waited on a
    request that could never return. The fix refuses over-long input up front, so
    the failure is an immediate message instead of a dead machine.
    """

    def test_over_long_audio_fails_with_an_actionable_message(self, tmp_path, monkeypatch):
        from src.webapp import jobs as jobs_mod

        monkeypatch.setattr(jobs_mod, "MAX_AUDIO_SECONDS", 2.0)
        sr = 44100
        long_wav = tmp_path / "long.wav"
        sf.write(long_wav, np.zeros(int(sr * 5), dtype=np.float32), sr, subtype="PCM_16")

        job = jobs_mod.process_upload("long.wav", long_wav.read_bytes())

        assert job.status == jobs_mod.STATUS_FAILED
        assert "minutes" in job.message
        # It must say what to do, not merely that it refused.
        assert "shorter" in job.message.lower() or "trim" in job.message.lower()

    def test_audio_within_the_limit_still_processes(self, tmp_path, monkeypatch):
        from src.webapp import jobs as jobs_mod

        monkeypatch.setattr(jobs_mod, "MAX_AUDIO_SECONDS", 60.0)
        with open(FIXTURE, "rb") as fh:
            job = jobs_mod.process_upload("vocal.wav", fh.read(), mode="modern_rap")
        assert job.status != jobs_mod.STATUS_FAILED, job.message


class TestUploadLimitIsSingleSourced:
    """Regression for the 2026-08-04 config drift.

    `MAX_UPLOAD_MB` was raised in Python, but the Dockerfile still pinned
    DRAKOTUNE_MAX_UPLOAD_MB=50 as an ENV, which silently won in production. A
    66.8 MB take kept being rejected with 413 after a full multi-minute upload,
    while the source said the limit was 160.
    """

    def test_dockerfile_env_matches_the_code_default(self):
        import re
        from src.webapp.app import MAX_UPLOAD_MB

        dockerfile = pathlib.Path("Dockerfile").read_text(encoding="utf-8")
        match = re.search(r"DRAKOTUNE_MAX_UPLOAD_MB=(\d+)", dockerfile)
        assert match, "Dockerfile no longer pins DRAKOTUNE_MAX_UPLOAD_MB"
        assert int(match.group(1)) == MAX_UPLOAD_MB, (
            f"Dockerfile pins {match.group(1)} MB but the code default is "
            f"{MAX_UPLOAD_MB} MB; the image value wins at runtime")

    def test_limits_are_published_so_the_client_need_not_hardcode_them(self):
        client = TestClient(app)
        limits = client.get("/api/modes").json()["limits"]
        from src.webapp.app import MAX_UPLOAD_MB
        from src.webapp.jobs import MAX_AUDIO_SECONDS

        assert limits["max_upload_mb"] == MAX_UPLOAD_MB
        assert limits["max_audio_seconds"] == MAX_AUDIO_SECONDS

    def test_client_does_not_hardcode_an_upload_limit(self):
        """The browser must learn the limit, not carry its own copy."""
        js = pathlib.Path("src/webapp/static/app.js").read_text(encoding="utf-8")
        assert "data.limits" in js, "client no longer reads limits from /api/modes"
