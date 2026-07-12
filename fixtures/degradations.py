"""Seeded synthetic vocal-degradation recipe library (M22).

Implements the degradation grid from docs/validation/DRAKOTUNE_ALPHA_VALIDATION_PLAN.md §2.
Every recipe is deterministic: (recipe id, seed, input audio) -> bit-identical
output, so degraded corpora are regenerable and never stored in git.

Honesty rule (research report §21): these are *models* of real defects. Results
on them are reported as synthetic; real-world claims need real recordings.

Families implemented here with numpy/pedalboard/pyloudnorm (existing deps):
  noise (room_tone | hvac | street-like), hum, clipping, reverb (synthetic IR),
  harshness boost, sibilance boost, proximity/mud shelf, low recording level.
The codec family (MP3 round-trip) uses FFmpeg via subprocess and is excluded
from bit-exact determinism guarantees (encoder builds vary); it is validated
for effect, not exactness.

Real noise beds (MUSAN) and measured IRs (OpenSLR-28/OpenAIR) plug into the
same interface once their manual download checkpoints are completed
(docs/data/DATASET_GOVERNANCE.md §4); recipes record their material source.
"""

import hashlib
import math
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pyloudnorm
import soundfile as sf
from pedalboard import HighShelfFilter, LowShelfFilter, Pedalboard, PeakFilter

DEGRADATION_LIBRARY_VERSION = "1.1.0"  # 1.1.0 (M32): plosive family


@dataclass(frozen=True)
class DegradationRecipe:
    """One reproducible degradation: family + severity + exact parameters."""

    id: str
    family: str
    severity: str            # mild | moderate | strong
    params: dict
    seed: int
    version: str = DEGRADATION_LIBRARY_VERSION
    material_source: str = "synthetic"  # later: "musan", "openslr28", ...

    def to_dict(self) -> dict:
        return {
            "id": self.id, "family": self.family, "severity": self.severity,
            "params": dict(self.params), "seed": self.seed,
            "version": self.version, "material_source": self.material_source,
        }


# --- primitive generators (all seeded) --------------------------------------

def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x)) + 1e-20))


def _shaped_noise(n: int, sr: int, seed: int, kind: str) -> np.ndarray:
    """White noise spectrally shaped into a rough environmental bed."""
    white = _rng(seed).standard_normal(n).astype(np.float32)
    spectrum = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    safe = np.maximum(freqs, 1.0)
    if kind == "room_tone":          # pink-ish: 1/sqrt(f)
        shape = 1.0 / np.sqrt(safe)
    elif kind == "hvac":             # heavy LF rumble: 1/f, cut above 400 Hz
        shape = 1.0 / safe
        shape[freqs > 400.0] *= 0.05
    elif kind == "street":           # broadband with LF weight: 1/f^0.7
        shape = 1.0 / (safe ** 0.7)
    else:
        raise ValueError(f"unknown noise kind: {kind}")
    shaped = np.fft.irfft(spectrum * shape, n=n).astype(np.float32)
    return shaped / (_rms(shaped) + 1e-12)


def _add_noise(audio: np.ndarray, sr: int, snr_db: float, kind: str, seed: int) -> np.ndarray:
    noise = _shaped_noise(len(audio), sr, seed, kind)
    noise_rms = _rms(audio) / (10.0 ** (snr_db / 20.0))
    return (audio + noise * noise_rms).astype(np.float32)


def _add_hum(audio: np.ndarray, sr: int, level_dbfs: float, base_hz: float, seed: int) -> np.ndarray:
    t = np.arange(len(audio), dtype=np.float64) / sr
    phase = _rng(seed).uniform(0, 2 * math.pi, size=4)
    hum = np.zeros_like(t)
    for k, amp in enumerate((1.0, 0.5, 0.25, 0.125)):
        hum += amp * np.sin(2 * math.pi * base_hz * (k + 1) * t + phase[k])
    hum = hum / (_rms(hum.astype(np.float32)) + 1e-12)
    return (audio + hum.astype(np.float32) * (10.0 ** (level_dbfs / 20.0))).astype(np.float32)


def _clip(audio: np.ndarray, clip_fraction: float) -> np.ndarray:
    """Hard-clip so that ~clip_fraction of samples sit at the ceiling."""
    magnitudes = np.abs(audio)
    threshold = float(np.quantile(magnitudes, 1.0 - clip_fraction))
    if threshold <= 0.0:
        return audio.copy()
    clipped = np.clip(audio, -threshold, threshold) / threshold  # ceiling at 1.0
    return clipped.astype(np.float32)


def _synthetic_reverb(audio: np.ndarray, sr: int, rt60_s: float, wet: float, seed: int) -> np.ndarray:
    """Convolve with a seeded exponentially decaying noise IR (synthetic room)."""
    ir_len = int(sr * min(rt60_s * 1.5, 3.0))
    t = np.arange(ir_len, dtype=np.float64) / sr
    ir = _rng(seed).standard_normal(ir_len) * np.exp(-6.9078 * t / rt60_s)  # -60 dB at rt60
    ir = (ir / (np.sqrt(np.sum(ir ** 2)) + 1e-12)).astype(np.float32)
    n = len(audio) + ir_len - 1
    wet_sig = np.fft.irfft(np.fft.rfft(audio, n) * np.fft.rfft(ir, n), n)[: len(audio)]
    wet_sig = wet_sig.astype(np.float32)
    scale = _rms(audio) / (_rms(wet_sig) + 1e-12)
    return ((1.0 - wet) * audio + wet * wet_sig * scale).astype(np.float32)


def _eq(audio: np.ndarray, sr: int, plugin) -> np.ndarray:
    return Pedalboard([plugin])(audio, sr).astype(np.float32)


def _to_level(audio: np.ndarray, sr: int, target_lufs: float) -> np.ndarray:
    """Gain to a target integrated LUFS (RMS-dBFS fallback for short signals)."""
    try:
        current = pyloudnorm.Meter(sr).integrated_loudness(audio.astype(np.float64))
        if not math.isfinite(current) or current <= -70.0:
            raise ValueError("unmeasurable")
    except Exception:
        current = 20.0 * math.log10(_rms(audio) + 1e-12)
    return (audio * (10.0 ** ((target_lufs - current) / 20.0))).astype(np.float32)


def _add_plosives(audio: np.ndarray, sr: int, count: int, amp: float, seed: int) -> np.ndarray:
    """Seeded low-frequency 'p/b' thumps: 50-90 Hz decaying bursts placed at
    energetic moments (a plosive rides the word onset, not silence)."""
    rng = _rng(seed)
    out = audio.copy()
    frame = sr // 10
    n_frames = max(len(audio) // frame - 1, 1)
    frame_rms = np.array([_rms(audio[i * frame:(i + 1) * frame]) for i in range(n_frames)])
    candidates = np.argsort(frame_rms)[-max(count * 3, count):]
    positions = rng.choice(candidates, size=min(count, len(candidates)), replace=False)
    burst_len = int(sr * 0.08)
    t = np.arange(burst_len) / sr
    for pos in sorted(positions):
        freq = float(rng.uniform(50.0, 90.0))
        thump = np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.018)
        i = pos * frame + int(rng.integers(0, frame // 2))
        end = min(i + burst_len, len(out))
        out[i:end] += (amp * _rms(audio) / 0.05) * thump[: end - i].astype(np.float32) * 0.5
    return np.clip(out, -1.0, 1.0).astype(np.float32)


def _codec_roundtrip(audio: np.ndarray, sr: int, bitrate_kbps: int) -> np.ndarray:
    """MP3 encode/decode via FFmpeg. Effect-validated, not bit-exact across builds."""
    with tempfile.TemporaryDirectory() as tmp:
        wav_in, mp3, wav_out = (Path(tmp) / n for n in ("in.wav", "mid.mp3", "out.wav"))
        sf.write(wav_in, audio, sr, subtype="PCM_16")
        for cmd in (
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_in),
             "-b:a", f"{bitrate_kbps}k", str(mp3)],
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3),
             "-ar", str(sr), "-ac", "1", str(wav_out)],
        ):
            subprocess.run(cmd, check=True, capture_output=True)
        out, _ = sf.read(wav_out, dtype="float32")
    if len(out) >= len(audio):          # codec delay padding: trim
        return out[: len(audio)].astype(np.float32)
    return np.pad(out, (0, len(audio) - len(out))).astype(np.float32)


# --- recipe application ------------------------------------------------------

def apply_recipe(audio: np.ndarray, sr: int, recipe: DegradationRecipe) -> np.ndarray:
    """Apply one recipe to mono float32 audio. Pure function of its inputs."""
    x = audio.astype(np.float32)
    p = recipe.params
    if recipe.family == "noise":
        return _add_noise(x, sr, p["snr_db"], p["kind"], recipe.seed)
    if recipe.family == "hum":
        return _add_hum(x, sr, p["level_dbfs"], p["base_hz"], recipe.seed)
    if recipe.family == "clipping":
        return _clip(x, p["clip_fraction"])
    if recipe.family == "reverb":
        return _synthetic_reverb(x, sr, p["rt60_s"], p["wet"], recipe.seed)
    if recipe.family == "harshness":
        return _eq(x, sr, PeakFilter(cutoff_frequency_hz=p["freq_hz"], gain_db=p["gain_db"], q=p["q"]))
    if recipe.family == "sibilance":
        return _eq(x, sr, HighShelfFilter(cutoff_frequency_hz=p["freq_hz"], gain_db=p["gain_db"], q=p["q"]))
    if recipe.family == "proximity":
        return _eq(x, sr, LowShelfFilter(cutoff_frequency_hz=p["freq_hz"], gain_db=p["gain_db"], q=p["q"]))
    if recipe.family == "low_level":
        return _to_level(x, sr, p["target_lufs"])
    if recipe.family == "plosive":
        return _add_plosives(x, sr, p["count"], p["amp"], recipe.seed)
    if recipe.family == "codec":
        return _codec_roundtrip(x, sr, p["bitrate_kbps"])
    raise ValueError(f"unknown degradation family: {recipe.family}")


def output_sha256(audio: np.ndarray) -> str:
    """Stable digest of a degraded result (float32 little-endian bytes)."""
    return hashlib.sha256(np.ascontiguousarray(audio, dtype="<f4").tobytes()).hexdigest()


# --- the standard grid (validation plan §2) ----------------------------------

def _grid() -> tuple[DegradationRecipe, ...]:
    recipes: list[DegradationRecipe] = []

    def add(family: str, severity: str, params: dict, seed: int) -> None:
        rid = f"{family}_{severity}" + (f"_{params['kind']}" if family == "noise" else "")
        recipes.append(DegradationRecipe(rid, family, severity, params, seed))

    for kind_i, kind in enumerate(("room_tone", "hvac", "street")):
        for sev, snr in (("mild", 20.0), ("moderate", 10.0), ("strong", 5.0)):
            add("noise", sev, {"snr_db": snr, "kind": kind}, seed=1000 + kind_i * 10 + int(snr))
    for sev, level in (("mild", -40.0), ("moderate", -30.0), ("strong", -20.0)):
        add("hum", sev, {"level_dbfs": level, "base_hz": 60.0}, seed=2000 + int(-level))
    for sev, frac in (("mild", 0.01), ("moderate", 0.03), ("strong", 0.08)):
        add("clipping", sev, {"clip_fraction": frac}, seed=0)
    for sev, (wet, rt60) in (("mild", (0.15, 0.4)), ("moderate", (0.30, 0.4)), ("strong", (0.50, 1.5))):
        add("reverb", sev, {"wet": wet, "rt60_s": rt60}, seed=3000 + int(wet * 100))
    for sev, gain in (("moderate", 4.0), ("strong", 8.0)):
        add("harshness", sev, {"freq_hz": 4000.0, "gain_db": gain, "q": 1.0}, seed=0)
    for sev, gain in (("moderate", 6.0), ("strong", 12.0)):
        add("sibilance", sev, {"freq_hz": 5500.0, "gain_db": gain, "q": 0.7}, seed=0)
    add("proximity", "moderate", {"freq_hz": 250.0, "gain_db": 6.0, "q": 0.7}, seed=0)
    for sev, lufs in (("moderate", -35.0), ("strong", -45.0)):
        add("low_level", sev, {"target_lufs": lufs}, seed=0)
    for sev, (count, amp) in (("moderate", (3, 0.5)), ("strong", (6, 0.9))):
        add("plosive", sev, {"count": count, "amp": amp}, seed=4000 + count)
    for sev, kbps in (("moderate", 96), ("strong", 64)):
        add("codec", sev, {"bitrate_kbps": kbps}, seed=0)

    return tuple(recipes)


STANDARD_GRID: tuple[DegradationRecipe, ...] = _grid()

# Families whose output is a pure numpy/pedalboard function of (input, seed):
# these carry a bit-exact regeneration guarantee. Codec is excluded by design.
DETERMINISTIC_FAMILIES = (
    "noise", "hum", "clipping", "reverb", "harshness",
    "sibilance", "proximity", "low_level", "plosive",
)
