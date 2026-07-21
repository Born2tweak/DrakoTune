"""DT-52 application/DSP seam characterization suite.

Acceptance (Field 13): baseline behavior unchanged (render parity), no UI/service
adapter imports backend internals. Adversarial (Field 16): unsupported
processor/parameter, backend unavailable, cancellation, partial output,
mismatched build.
"""

import numpy as np
import pytest
import soundfile as sf

from src.application import (
    ApplicationService,
    BackendUnavailable,
    DspBackend,
    PedalboardBackend,
    UnavailableBackend,
)
from src.dsp_engine import PROCESSORS, execute_plan, render_plan
from src.evaluation.semantics.enums import ResultStatus
from src.shared_types import ProcessingAction, ProcessingPlan

SR = 44100


def _tone(freq=200.0, seconds=0.5, sr=SR):
    t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
    return (0.2 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def _plan():
    return ProcessingPlan(
        id="p",
        actions=(
            ProcessingAction(id="a1", processor="HighpassFilter",
                             parameters={"cutoff_frequency_hz": 90.0}, objective_id="obj.rumble"),
            ProcessingAction(id="a2", processor="PeakFilter",
                             parameters={"cutoff_frequency_hz": 3500.0, "gain_db": -4.0, "q": 1.4},
                             objective_id="obj.harshness"),
        ),
    )


# --------------------------------------------------------------------------
# Backend contract
# --------------------------------------------------------------------------

def test_pedalboard_backend_satisfies_protocol_and_declares_license():
    b = PedalboardBackend()
    assert isinstance(b, DspBackend)
    assert b.license_id == "GPL-3.0-only"  # GPL captured, not hidden
    caps = b.capabilities()
    assert set(caps.processors) == set(PROCESSORS)
    assert caps.engine_version


def test_unsupported_processor_and_param_rejected():
    b = PedalboardBackend()
    ok, reasons = b.supports("NotAProcessor", {})
    assert not ok and any("unsupported_processor" in r for r in reasons)
    ok2, reasons2 = b.supports("Gain", {"bogus_param": 1.0})
    assert not ok2 and any("unknown_param" in r for r in reasons2)


def test_service_validate_plan_flags_unsupported_action():
    svc = ApplicationService()
    bad = ProcessingPlan(id="p", actions=(ProcessingAction(id="a", processor="NotAProcessor", parameters={}),))
    ok, reasons = svc.validate_plan(bad)
    assert not ok
    assert any("unsupported_processor" in r for r in reasons)


# --------------------------------------------------------------------------
# Behavior parity — the seam changes no sound
# --------------------------------------------------------------------------

def test_render_array_is_bit_identical_to_engine():
    audio = _tone()
    plan = _plan()
    svc = ApplicationService()
    via_service, result = svc.render_array(audio.copy(), SR, plan)
    direct, _ = execute_plan(audio.copy(), SR, plan)
    assert result.status is ResultStatus.PASSED
    np.testing.assert_array_equal(via_service, direct)


def test_render_file_matches_render_plan(tmp_path):
    audio = _tone()
    src = tmp_path / "in.wav"
    sf.write(src, audio, SR, subtype="PCM_16")
    plan = _plan()

    out_service = tmp_path / "svc.wav"
    out_direct = tmp_path / "direct.wav"
    ApplicationService().render(str(src), str(out_service), plan)
    render_plan(str(src), str(out_direct), plan)

    a, _ = sf.read(out_service, dtype="float32")
    b, _ = sf.read(out_direct, dtype="float32")
    np.testing.assert_array_equal(a, b)


def test_render_result_carries_backend_license_identity(tmp_path):
    audio = _tone()
    src = tmp_path / "in.wav"
    sf.write(src, audio, SR, subtype="PCM_16")
    res = ApplicationService().render(str(src), str(tmp_path / "o.wav"), _plan())
    assert res.status is ResultStatus.PASSED
    assert res.build.backend_license == "GPL-3.0-only"


# --------------------------------------------------------------------------
# Dependency inversion — service works against a fake backend
# --------------------------------------------------------------------------

class _FakeBackend:
    name = "fake"
    license_id = "test"

    def capabilities(self):
        from src.application.backend import BackendCapabilities
        return BackendCapabilities(("Gain",), {"Gain": {"gain_db": (-24.0, 12.0)}}, False, 0, "9.9.9")

    def supports(self, processor, params):
        return processor == "Gain", () if processor == "Gain" else ("unsupported_processor",)

    def render(self, audio, sample_rate, plan):
        from src.dsp_engine.executor import ExecutionResult
        return audio * 0.5, ExecutionResult()


def test_service_uses_injected_backend_not_library_internals():
    svc = ApplicationService(backend=_FakeBackend())
    out, res = svc.render_array(_tone(), SR, ProcessingPlan(id="p"))
    assert res.build.backend_name == "fake"
    assert res.build.engine_version == "9.9.9"


# --------------------------------------------------------------------------
# Adversarial: unavailable backend, cancellation, build mismatch
# --------------------------------------------------------------------------

def test_backend_unavailable_is_typed_error_not_crash(tmp_path):
    audio = _tone()
    src = tmp_path / "in.wav"
    sf.write(src, audio, SR, subtype="PCM_16")
    svc = ApplicationService(backend=UnavailableBackend())
    res = svc.render(str(src), str(tmp_path / "o.wav"), _plan())
    assert res.status is ResultStatus.ERROR
    assert "backend_unavailable" in res.reasons


def test_cancellation_before_render_writes_no_output(tmp_path):
    audio = _tone()
    src = tmp_path / "in.wav"
    sf.write(src, audio, SR, subtype="PCM_16")
    out = tmp_path / "o.wav"
    res = ApplicationService().render(str(src), str(out), _plan(), cancel=lambda: True)
    assert res.status is ResultStatus.CANCELLED
    assert not out.exists()


def test_build_mismatch_blocks_render(tmp_path):
    audio = _tone()
    src = tmp_path / "in.wav"
    sf.write(src, audio, SR, subtype="PCM_16")
    res = ApplicationService().render(
        str(src), str(tmp_path / "o.wav"), _plan(), expected_engine_version="0.0.0-wrong"
    )
    assert res.status is ResultStatus.ERROR
    assert any("build_mismatch" in r for r in res.reasons)


def test_missing_input_is_typed_error(tmp_path):
    res = ApplicationService().render(str(tmp_path / "nope.wav"), str(tmp_path / "o.wav"), _plan())
    assert res.status is ResultStatus.ERROR
    assert any("decode_failed" in r for r in res.reasons)


# --------------------------------------------------------------------------
# No UI/service adapter imports DSP library internals
# --------------------------------------------------------------------------

def test_application_layer_does_not_import_pedalboard_at_top_level():
    import ast
    import pathlib

    root = pathlib.Path("src/application")
    offenders = []
    for py in root.glob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                offenders += [n.name for n in node.names if n.name.split(".")[0] == "pedalboard"]
            elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("pedalboard"):
                offenders.append(node.module)
    assert offenders == [], f"application layer imports DSP internals: {offenders}"
