"""Deterministic fixture loader (M02).

Loads committed synthetic fixtures and their declared metadata. Diagnostics,
DSP, evaluation, and report tests use this as their shared regression material.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
EXPECTED_DIR = BASE_DIR / "expected"


@dataclass(frozen=True)
class Fixture:
    """A loaded fixture: its audio, sample rate, and declared metadata."""

    name: str
    audio: np.ndarray
    sample_rate: int
    metadata: dict


def list_fixtures() -> list[str]:
    """Return fixture names (sorted) discovered from the expected/ manifests."""
    return sorted(p.stem for p in EXPECTED_DIR.glob("*.json"))


def load_metadata(name: str) -> dict:
    """Load the declared metadata for a fixture."""
    path = EXPECTED_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No fixture metadata for '{name}' at {path}")
    return json.loads(path.read_text())


def load_fixture(name: str) -> Fixture:
    """Load a fixture's audio and metadata deterministically."""
    meta = load_metadata(name)
    wav_path = BASE_DIR / meta["audio_path"]
    if not wav_path.exists():
        raise FileNotFoundError(f"No fixture audio for '{name}' at {wav_path}")
    audio, sample_rate = sf.read(str(wav_path), dtype="float32")
    return Fixture(name=name, audio=audio, sample_rate=int(sample_rate), metadata=meta)
