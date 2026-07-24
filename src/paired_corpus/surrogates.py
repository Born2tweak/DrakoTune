"""Ground-truth surrogate pair factory (DT-55B/C test harness).

Manufactures exact raw/wet pairs from a synthetic 'performance' we own:
  clean  = vocal-like phrase bursts (harmonics + vibrato + consonant noise)
  raw    = clean + noise floor + low-mid 'boxiness' boost + room comb
  wet    = known chain over clean: phrase leveling, low-mid cut, compression,
           peak normalization  (parameters logged in TRUTH)
Every pairing/alignment/delta component is validated against these known answers
before touching any gated audio.
"""
from __future__ import annotations

import numpy as np

SR = 44100

TRUTH = {
    "lowmid_cut_db": -4.0,        # wet cuts 250-500 -> d_lowmid < 0
    "compression": True,           # -> d_crest < 0
    "phrase_leveling": True,       # -> wet phrase-RMS spread < raw spread
    "raw_noise_floor_db": -45.0,   # wet built from clean -> d_noise_floor < 0
}


def _phrase(sr: int, dur_s: float, f0: float, level: float,
            rng: np.random.Generator) -> np.ndarray:
    n = int(dur_s * sr)
    t = np.arange(n) / sr
    vib = 1.0 + 0.01 * np.sin(2 * np.pi * 5.5 * t)
    x = np.zeros(n)
    for k, amp in ((1, 1.0), (2, 0.5), (3, 0.33), (4, 0.2), (6, 0.1)):
        x += amp * np.sin(2 * np.pi * f0 * k * vib * t + rng.uniform(0, 6.28))
    env = np.minimum(t / 0.03, 1.0) * np.minimum((dur_s - t) / 0.08, 1.0)
    x *= np.clip(env, 0, 1)
    # consonant: 30 ms noise burst at the start
    c = int(0.03 * sr)
    x[:c] += rng.standard_normal(c) * 0.4 * np.linspace(1, 0, c)
    x *= level / (np.max(np.abs(x)) + 1e-12)
    return x


def make_performance(seed: int, n_phrases: int = 5) -> np.ndarray:
    """Phrase bursts with varying levels (so leveling is measurable) + pauses."""
    rng = np.random.default_rng(seed)
    parts: list[np.ndarray] = [np.zeros(int(0.3 * SR))]
    for i in range(n_phrases):
        level = rng.uniform(0.25, 0.85)
        f0 = rng.uniform(140, 320)
        parts.append(_phrase(SR, rng.uniform(0.6, 1.2), f0, level, rng))
        parts.append(np.zeros(int(rng.uniform(0.35, 0.6) * SR)))
    return np.concatenate(parts).astype(np.float32)


def _band_gain(x: np.ndarray, sr: int, lo: float, hi: float, gain_db: float) -> np.ndarray:
    spec = np.fft.rfft(x.astype(np.float64))
    freqs = np.fft.rfftfreq(len(x), 1.0 / sr)
    g = np.ones_like(freqs)
    g[(freqs >= lo) & (freqs <= hi)] = 10 ** (gain_db / 20)
    return np.fft.irfft(spec * g, len(x))


def degrade_to_raw(clean: np.ndarray, seed: int) -> np.ndarray:
    """Noise floor + boxiness + short room comb = a 'weak mic in a room'."""
    rng = np.random.default_rng(seed + 1)
    x = _band_gain(clean, SR, 250, 500, +5.0)                    # boxy boost
    d = int(0.011 * SR)                                          # 11 ms comb
    room = np.copy(x)
    room[d:] += 0.35 * x[:-d]
    noise = rng.standard_normal(len(x)) * (10 ** (TRUTH["raw_noise_floor_db"] / 20))
    out = room + noise
    return (out / (np.max(np.abs(out)) + 1e-12) * 0.7).astype(np.float32)


def pro_chain_to_wet(clean: np.ndarray) -> np.ndarray:
    """The known 'professional' chain (documented in TRUTH)."""
    from src.paired_corpus.alignment import segment_phrases

    x = clean.astype(np.float64).copy()
    # 1. Phrase leveling toward a common RMS target.
    phrases = segment_phrases(clean, SR)
    if phrases:
        targets = []
        for a, b in phrases:
            seg = x[int(a * SR):int(b * SR)]
            targets.append(np.sqrt(np.mean(seg**2) + 1e-20))
        ref = float(np.median(targets))
        for (a, b), rms in zip(phrases, targets):
            i, j = int(a * SR), int(b * SR)
            x[i:j] *= np.clip(ref / (rms + 1e-20), 0.5, 2.0)
    # 2. Low-mid cut.
    x = _band_gain(x, SR, 250, 500, TRUTH["lowmid_cut_db"])
    # 3. Compression (soft-knee static curve on the sample magnitude).
    t, ratio = 0.3, 3.0
    mag = np.abs(x)
    over = mag > t
    x[over] = np.sign(x[over]) * (t + (mag[over] - t) / ratio)
    # 4. Peak normalize to -1.5 dBFS.
    return (x / (np.max(np.abs(x)) + 1e-12) * 10 ** (-1.5 / 20)).astype(np.float32)


def make_surrogate_pair(seed: int, wet_delay_s: float = 0.0
                        ) -> tuple[np.ndarray, np.ndarray, int, dict]:
    """(raw, wet, sr, truth). Optional wet_delay_s prepends silence to the wet
    side so offset recovery is testable against a known answer."""
    clean = make_performance(seed)
    raw = degrade_to_raw(clean, seed)
    wet = pro_chain_to_wet(clean)
    if wet_delay_s > 0:
        wet = np.concatenate([np.zeros(int(wet_delay_s * SR), dtype=np.float32), wet])
    return raw, wet, SR, dict(TRUTH)
