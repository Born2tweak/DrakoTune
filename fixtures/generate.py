"""Deterministic synthetic audio fixture generator (M02).

Fixtures are SYNTHETIC by policy — never real user vocals (privacy + copyright).
Every fixture is produced from a fixed seed so the committed WAV bytes are
reproducible. Regenerate with:

    python fixtures/generate.py

Each fixture writes two files:
    fixtures/audio/<name>.wav        44100 Hz, mono, PCM_16
    fixtures/expected/<name>.json    declared metadata + informational expectations

The `expected_diagnoses` fields are INFORMATIONAL in M02. Diagnostic thresholds
are not yet calibrated, so tests must not assert them until M04-M06 pin them.
"""

import json
from pathlib import Path

import numpy as np
import soundfile as sf

SAMPLE_RATE = 44100
DURATION_SECONDS = 1.0
BASE_DIR = Path(__file__).resolve().parent


def _t() -> np.ndarray:
    return np.linspace(0, DURATION_SECONDS, int(SAMPLE_RATE * DURATION_SECONDS), endpoint=False)


def _clean_tone() -> np.ndarray:
    """Harmonic, vocal-like signal with gentle high-frequency content."""
    t = _t()
    sig = np.zeros_like(t)
    for n in range(1, 16):
        freq = 150 * n
        if freq > SAMPLE_RATE // 2:
            break
        sig += (0.3 / (n**1.2)) * np.sin(2 * np.pi * freq * t)
    sig += 0.004 * np.random.default_rng(1001).standard_normal(len(t))
    return sig / np.max(np.abs(sig)) * 0.5


def _harsh() -> np.ndarray:
    """Fundamental plus strong narrow upper-mid energy (ice-pick harshness)."""
    t = _t()
    sig = 0.4 * np.sin(2 * np.pi * 200 * t)
    sig += 0.3 * np.sin(2 * np.pi * 3500 * t)
    sig += 0.2 * np.sin(2 * np.pi * 6500 * t)
    return np.clip(sig, -0.95, 0.95)


def _muddy() -> np.ndarray:
    """Excess low-mid energy around 300 Hz."""
    t = _t()
    sig = 0.6 * np.sin(2 * np.pi * 300 * t)
    sig += 0.08 * np.sin(2 * np.pi * 1500 * t)
    return np.clip(sig, -0.95, 0.95)


def _noisy() -> np.ndarray:
    """Quiet tone over an elevated broadband noise floor."""
    t = _t()
    sig = 0.2 * np.sin(2 * np.pi * 220 * t)
    sig += 0.03 * np.random.default_rng(2002).standard_normal(len(t))
    return np.clip(sig, -0.95, 0.95)


def _clipped() -> np.ndarray:
    """Hard-clipped sine — permanent full-scale plateaus."""
    t = _t()
    return np.clip(np.sin(2 * np.pi * 440 * t) * 2.0, -1.0, 1.0)


def _silence() -> np.ndarray:
    """Near-digital-silence (tiny dither so it is not a pure zero buffer)."""
    return 1e-5 * np.random.default_rng(3003).standard_normal(int(SAMPLE_RATE * DURATION_SECONDS))


FIXTURE_SPECS: dict[str, dict] = {
    "clean_tone": {
        "builder": _clean_tone,
        "category": "clean",
        "description": "Harmonic vocal-like tone with gentle highs; minimal issues expected.",
        "expected_diagnoses": {"harshness": "low", "muddiness": "low"},
    },
    "harsh": {
        "builder": _harsh,
        "category": "harsh",
        "description": "Strong narrow energy at 3.5kHz and 6.5kHz over a 200Hz fundamental.",
        "expected_diagnoses": {"harshness": "elevated"},
    },
    "muddy": {
        "builder": _muddy,
        "category": "muddy",
        "description": "Dominant 300Hz low-mid buildup with little clarity band energy.",
        "expected_diagnoses": {"muddiness": "elevated"},
    },
    "noisy": {
        "builder": _noisy,
        "category": "noisy",
        "description": "Quiet 220Hz tone over an elevated broadband noise floor.",
        "expected_diagnoses": {"noise_floor": "elevated"},
    },
    "clipped": {
        "builder": _clipped,
        "category": "clipped",
        "description": "Hard-clipped 440Hz sine; broadband distortion from full-scale plateaus.",
        "expected_diagnoses": {"clipping": "elevated"},
    },
    "silence": {
        "builder": _silence,
        "category": "silence",
        "description": "Near-digital-silence; used to check graceful handling of empty input.",
        "expected_diagnoses": {},
    },
}


def write_fixtures(base_dir: Path = BASE_DIR) -> list[str]:
    """Write all fixture WAVs and expected JSON. Returns the names written."""
    audio_dir = base_dir / "audio"
    expected_dir = base_dir / "expected"
    audio_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for name, spec in FIXTURE_SPECS.items():
        signal = spec["builder"]().astype(np.float32)
        wav_path = audio_dir / f"{name}.wav"
        sf.write(str(wav_path), signal, SAMPLE_RATE, subtype="PCM_16")

        meta = {
            "name": name,
            "category": spec["category"],
            "description": spec["description"],
            "sample_rate": SAMPLE_RATE,
            "channels": 1,
            "duration_seconds": DURATION_SECONDS,
            "subtype": "PCM_16",
            "audio_path": f"audio/{name}.wav",
            "expected_diagnoses": spec["expected_diagnoses"],
        }
        (expected_dir / f"{name}.json").write_text(json.dumps(meta, indent=2) + "\n")
        written.append(name)

    return written


if __name__ == "__main__":
    names = write_fixtures()
    print(f"Wrote {len(names)} fixtures: {', '.join(names)}")
