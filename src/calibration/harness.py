"""Calibration harness (M17).

Moves diagnostic thresholds from "hand-set" toward "evidence-based" by measuring
how the current analyzers behave on a deterministic set of *labeled* synthetic
signals: how often a known issue is detected (true-positive rate) and how often
a clean control trips a detector (false-positive rate).

This harness only MEASURES. It never silently changes thresholds — that would
violate "never change thresholds just to make tests pass". Its output is
evidence for humans to adjust thresholds deliberately (and bump analyzer
versions when they do).
"""

from dataclasses import dataclass

import numpy as np

from src.diagnostics import interpret_spectral, measure_safety, measure_spectral

SR = 44100
CALIBRATION_VERSION = "1.0.0"

# Issues this harness generates positives/controls for.
ISSUES = ("harshness", "muddiness", "sibilance", "noise_floor", "clipping")


@dataclass(frozen=True)
class LabeledSample:
    name: str
    audio: np.ndarray
    issue: str | None  # None => clean control
    intensity: str  # "clean" | "mild" | "strong"


def _phrased(sig: np.ndarray, block: float = 0.3, gap: float = 0.15) -> np.ndarray:
    """Apply a voiced/unvoiced envelope so silent gaps exist (realistic floor)."""
    env = np.zeros_like(sig)
    n_block, n_gap = int(SR * block), int(SR * gap)
    i = 0
    on = True
    while i < len(sig):
        seg = n_block if on else n_gap
        if on:
            env[i:i + seg] = 1.0
        i += seg
        on = not on
    return (sig * env).astype(np.float32)


def _t(seconds: float) -> np.ndarray:
    return np.linspace(0, seconds, int(SR * seconds), endpoint=False)


def _clean(seed: int, seconds: float = 1.5) -> np.ndarray:
    t = _t(seconds)
    sig = np.zeros_like(t)
    for n in range(1, 16):
        f = 150 * n
        if f > SR // 2:
            break
        sig += (0.3 / (n**1.2)) * np.sin(2 * np.pi * f * t)
    sig += 0.002 * np.random.default_rng(seed).standard_normal(len(t))
    sig = _phrased(sig)
    return (sig / (np.max(np.abs(sig)) + 1e-9) * 0.5).astype(np.float32)


def _harsh(seed: int) -> np.ndarray:
    t = _t(1.5)
    sig = 0.35 * np.sin(2 * np.pi * 200 * t) + 0.32 * np.sin(2 * np.pi * 3600 * t)
    return _phrased(np.clip(sig, -0.95, 0.95))


def _muddy(seed: int) -> np.ndarray:
    t = _t(1.5)
    sig = 0.6 * np.sin(2 * np.pi * 300 * t) + 0.06 * np.sin(2 * np.pi * 2000 * t)
    return _phrased(np.clip(sig, -0.95, 0.95))


def _sibilant(seed: int) -> np.ndarray:
    t = _t(1.5)
    sig = 0.18 * np.sin(2 * np.pi * 250 * t) + 0.5 * np.sin(2 * np.pi * 6800 * t)
    return _phrased(np.clip(sig, -0.95, 0.95))


def _noisy(seed: int) -> np.ndarray:
    t = _t(1.5)
    sig = 0.2 * np.sin(2 * np.pi * 220 * t)
    sig = _phrased(sig)
    sig += 0.05 * np.random.default_rng(seed).standard_normal(len(sig))  # floor fills gaps
    return np.clip(sig, -0.95, 0.95).astype(np.float32)


def _clipped(seed: int) -> np.ndarray:
    t = _t(1.5)
    return _phrased(np.clip(np.sin(2 * np.pi * 300 * t) * 2.0, -1.0, 1.0))


_GENERATORS = {
    "harshness": _harsh,
    "muddiness": _muddy,
    "sibilance": _sibilant,
    "noise_floor": _noisy,
    "clipping": _clipped,
}


def build_samples(n_per_issue: int = 3, n_clean: int = 4) -> list[LabeledSample]:
    """Deterministic labeled set: strong positives per issue + clean controls."""
    samples: list[LabeledSample] = []
    for issue, gen in _GENERATORS.items():
        for k in range(n_per_issue):
            samples.append(LabeledSample(f"{issue}_{k}", gen(1000 + k), issue, "strong"))
    for k in range(n_clean):
        samples.append(LabeledSample(f"clean_{k}", _clean(500 + k), None, "clean"))
    return samples


def detect_issues(audio: np.ndarray, sr: int = SR) -> set[str]:
    """Which issues the current analyzers flag for a signal."""
    found: set[str] = set()
    obs, _ = measure_spectral(audio, sr)
    for interp in interpret_spectral(obs):
        found.add(interp.issue)
    _, flags, _ = measure_safety(audio, sr)
    if "clipping" in flags:
        found.add("clipping")
    return found


@dataclass(frozen=True)
class IssueStats:
    issue: str
    true_positive_rate: float
    false_positive_rate: float
    n_positive: int
    n_clean: int


def calibrate(samples: list[LabeledSample] | None = None) -> dict:
    """Run detection over the labeled set and return per-issue TPR/FPR."""
    samples = samples or build_samples()
    detections = {s.name: detect_issues(s.audio) for s in samples}
    clean = [s for s in samples if s.issue is None]

    stats: list[IssueStats] = []
    for issue in ISSUES:
        positives = [s for s in samples if s.issue == issue]
        tp = sum(1 for s in positives if issue in detections[s.name])
        fp = sum(1 for s in clean if issue in detections[s.name])
        stats.append(IssueStats(
            issue=issue,
            true_positive_rate=round(tp / len(positives), 3) if positives else 0.0,
            false_positive_rate=round(fp / len(clean), 3) if clean else 0.0,
            n_positive=len(positives),
            n_clean=len(clean),
        ))

    return {
        "calibration_version": CALIBRATION_VERSION,
        "n_samples": len(samples),
        "issues": {s.issue: {
            "tpr": s.true_positive_rate,
            "fpr": s.false_positive_rate,
            "n_positive": s.n_positive,
            "n_clean": s.n_clean,
        } for s in stats},
    }
