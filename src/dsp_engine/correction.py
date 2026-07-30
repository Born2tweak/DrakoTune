"""Pitch correction curve: contour -> scale target -> curve (DT-100, stages 2-3).

R1 (`pitch.py`) measures where the voice is. R2 (`psola.py`) moves it. This is
the part in between that decides *where to move it to*, and it is deliberately
the smallest, most inspectable piece of the three: every value is authored and
bounded, nothing is searched, and no automated objective selects anything — so
none of it depends on Q-016 being resolved.

The design commitments worth stating, because each one is a decision that could
have gone the other way:

  * **A deadband.** Deviation inside it is left alone. Vibrato, scoops, bent
    notes and slides are all "wrong" against equal temperament, and a corrector
    without a deadband flattens the performance into a test tone. The deadband is
    what separates correcting a note from erasing a singer.
  * **Retune speed, not just depth.** Instant correction is the recognisable
    hard-tuned artifact; a finite glide is what makes correction inaudible. Speed
    is expressed in milliseconds to reach the target, so it means something
    physical rather than being a 0-1 knob.
  * **Unvoiced frames are never corrected.** There is no pitch to correct in a
    consonant or a breath, and pulling one toward a note is pure damage.
  * **Correction is bounded.** A curve is clamped to a maximum number of cents,
    so a tracking error cannot produce a large confident shift.

Nothing here is promoted, and no surface may call this tuning until the listening
question in Q-016 is settled.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.dsp_engine.pitch import F0Track

# Twelve-tone equal temperament, A440. Semitone indices within an octave.
_CHROMATIC = tuple(range(12))
SCALES: dict[str, tuple[int, ...]] = {
    "chromatic": _CHROMATIC,
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),           # natural minor
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
    "pentatonic_minor": (0, 3, 5, 7, 10),
    "pentatonic_major": (0, 2, 4, 7, 9),
}
NOTES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Bounds. These are limits on what may be authored, not tuned values.
MAX_CORRECTION_CENTS = 100.0     # never move a note by more than a semitone
MIN_RETUNE_MS = 1.0
MAX_RETUNE_MS = 500.0
MAX_DEADBAND_CENTS = 100.0


@dataclass(frozen=True)
class CorrectionSettings:
    """One authored correction character.

    `strength` 0 leaves the take alone; 1 pulls fully to the target. `retune_ms`
    is how long the glide toward a new target takes. `deadband_cents` is how far
    the voice may stray before anything happens at all.
    """

    strength: float = 0.7
    retune_ms: float = 60.0
    deadband_cents: float = 20.0
    scale: str = "chromatic"
    key: str = "C"
    max_correction_cents: float = MAX_CORRECTION_CENTS

    def validated(self) -> CorrectionSettings:
        if self.scale not in SCALES:
            raise ValueError(f"unknown scale {self.scale!r}; have {sorted(SCALES)}")
        if self.key not in NOTES:
            raise ValueError(f"unknown key {self.key!r}; have {list(NOTES)}")
        return CorrectionSettings(
            strength=float(np.clip(self.strength, 0.0, 1.0)),
            retune_ms=float(np.clip(self.retune_ms, MIN_RETUNE_MS, MAX_RETUNE_MS)),
            deadband_cents=float(np.clip(self.deadband_cents, 0.0, MAX_DEADBAND_CENTS)),
            scale=self.scale, key=self.key,
            max_correction_cents=float(
                np.clip(self.max_correction_cents, 0.0, MAX_CORRECTION_CENTS)),
        )


# Three authored characters. They differ in kind, not only in degree: Natural
# leaves a wide deadband and glides slowly, Hard removes the deadband and snaps.
PRESETS: dict[str, CorrectionSettings] = {
    "natural": CorrectionSettings(strength=0.5, retune_ms=120.0, deadband_cents=35.0),
    "modern": CorrectionSettings(strength=0.8, retune_ms=40.0, deadband_cents=15.0),
    "hard": CorrectionSettings(strength=1.0, retune_ms=1.0, deadband_cents=0.0),
}


def scale_degrees(key: str, scale: str) -> tuple[int, ...]:
    """Absolute semitone classes (0-11) of a scale in a key."""
    if scale not in SCALES:
        raise ValueError(f"unknown scale {scale!r}")
    if key not in NOTES:
        raise ValueError(f"unknown key {key!r}")
    root = NOTES.index(key)
    return tuple(sorted((root + d) % 12 for d in SCALES[scale]))


def _hz_to_midi(f0: np.ndarray) -> np.ndarray:
    return 69.0 + 12.0 * np.log2(np.maximum(f0, 1e-9) / 440.0)


def nearest_scale_target(f0_hz: np.ndarray, key: str, scale: str) -> np.ndarray:
    """Nearest in-scale pitch (in MIDI numbers) for each frame; NaN stays NaN."""
    degrees = np.asarray(scale_degrees(key, scale), dtype=np.float64)
    midi = _hz_to_midi(np.asarray(f0_hz, dtype=np.float64))
    out = np.full(midi.shape, np.nan)
    finite = np.isfinite(midi)
    if not np.any(finite):
        return out

    values = midi[finite]
    # Candidate targets are every scale degree in the octave below and above, so
    # a note just under C can snap up to C rather than down to the octave's B.
    octaves = np.floor(values / 12.0)[:, None]
    candidates = np.concatenate([
        (octaves + shift) * 12.0 + degrees[None, :] for shift in (-1.0, 0.0, 1.0)
    ], axis=1)
    best = np.argmin(np.abs(candidates - values[:, None]), axis=1)
    out[finite] = candidates[np.arange(values.size), best]
    return out


def correction_cents(track: F0Track, settings: CorrectionSettings) -> np.ndarray:
    """Per-frame correction in cents. Zero where nothing should happen.

    Unvoiced frames get exactly 0: there is no pitch there to correct.
    """
    settings = settings.validated()
    target_midi = nearest_scale_target(track.f0_hz, settings.key, settings.scale)
    midi = _hz_to_midi(track.f0_hz)

    cents = np.zeros(track.f0_hz.shape, dtype=np.float64)
    usable = np.isfinite(midi) & np.isfinite(target_midi)
    if not np.any(usable):
        return cents

    error = (target_midi[usable] - midi[usable]) * 100.0     # cents to the target
    # Deadband: inside it, leave the performance alone entirely. Outside it, only
    # the excess is corrected, so the curve is continuous at the boundary rather
    # than jumping the full deadband width the moment it is crossed.
    magnitude = np.abs(error)
    excess = np.maximum(magnitude - settings.deadband_cents, 0.0)
    corrected = np.sign(error) * excess * settings.strength
    cents[usable] = np.clip(corrected,
                            -settings.max_correction_cents,
                            settings.max_correction_cents)
    return cents


def _glide(cents: np.ndarray, hop_ms: float, retune_ms: float) -> np.ndarray:
    """One-pole glide toward each new target, so correction is not instantaneous.

    An instant jump to the target is the recognisable hard-tuned sound. `retune_ms`
    is the time constant; at MIN_RETUNE_MS the filter is effectively bypassed,
    which is what the `hard` preset wants.
    """
    if retune_ms <= MIN_RETUNE_MS or cents.size == 0:
        return cents
    alpha = float(np.exp(-hop_ms / retune_ms))
    out = np.empty_like(cents)
    acc = 0.0
    for i, value in enumerate(cents):
        acc = alpha * acc + (1.0 - alpha) * float(value)
        out[i] = acc
    return out


def correction_curve(track: F0Track, settings: CorrectionSettings,
                     n_samples: int, sample_rate: int) -> np.ndarray:
    """A per-sample ratio curve ready for `psola.shift_pitch`.

    Frame-rate correction is glided and then interpolated to sample rate, so the
    curve that reaches the resynthesiser has no steps in it.
    """
    settings = settings.validated()
    cents = _glide(correction_cents(track, settings), track.hop_ms, settings.retune_ms)
    if n_samples <= 0:
        return np.ones(0, dtype=np.float64)
    if cents.size == 0:
        return np.ones(n_samples, dtype=np.float64)

    frame_positions = track.times_s * sample_rate
    per_sample = np.interp(np.arange(n_samples, dtype=np.float64),
                           frame_positions, cents, left=cents[0], right=cents[-1])
    return 2.0 ** (per_sample / 1200.0)
