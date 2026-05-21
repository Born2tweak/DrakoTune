# Alpha Diagnosis Iteration Plan

> Milestone Alpha 2: Diagnostic Audio Intelligence Layer
> Created: 2026-05-20
> Status: DRAFT — awaiting review

---

## 1. The Problem

The Alpha real vocal test (Headlock, 162s) revealed that a generic cleanup chain produces barely audible change. The pipeline applies the same EQ cuts, compression, and gating regardless of what is actually wrong with the input vocal. This is a preset, not intelligence.

DrakoTune's core promise is not "apply cleanup." It is: **diagnose what is wrong, then respond.**

A raw underground vocal can suffer from many different problems. Applying a mud cut to a vocal that is already thin makes it worse. Applying harshness reduction to a dull vocal kills what little presence it has. The system must listen first, then act.

---

## 2. Philosophy

### What "Better" Means for DrakoTune

The goal is NOT "technically clean." The goal is making raw underground vocals sound:
- **More expensive** — harmonic richness, controlled dynamics, spatial depth
- **Smoother** — no ear fatigue, no harsh transients, consistent energy
- **Clearer** — every word audible, consonants defined, no masking
- **Emotionally listenable** — the listener focuses on the performance, not the recording flaws

### Diagnosis Before Processing

Every raw vocal file must pass through a diagnostic layer before any DSP is applied. The diagnostic layer produces a **VocalProfile** — a structured report of what is wrong, how severe each problem is, and what DSP actions are recommended.

The diagnostic layer does NOT process audio. It analyzes and recommends. The DSP layer then executes the recommendations.

---

## 3. Diagnosis Categories

Each category defines: what it sounds like, how to measure it, where it lives in the spectrum, how to detect it, what DSP fixes it, and the risk of making it worse.

---

### 3.1 Harshness

| Field | Value |
|---|---|
| **Audible symptom** | Ear fatigue within 30 seconds. Vocals sound sharp, aggressive, "ice pick" quality. Painful to listen to at normal volume. |
| **Measurable signal feature** | Elevated RMS energy in 2.5–6kHz band relative to overall vocal RMS. Spectral centroid skewed high. High crest factor in harsh band. |
| **Likely frequency range** | 2.5–6kHz (primary), 6–10kHz (secondary digital harshness) |
| **Detection method** | **Librosa:** Compute spectral energy in 2.5–6kHz band vs 200Hz–2kHz band. Ratio > 0.35 indicates harshness. Use `librosa.feature.spectral_contrast` to measure peak-to-valley variance in upper-mids. High variance = resonant peaks = harshness. **Essentia:** `SpectralContrast` and `Dissonance` descriptors. High dissonance in 3–5kHz = harshness. |
| **DSP response** | **Pedalboard:** `PeakFilter` with cut at detected peak frequency (not fixed). Q = 1.0–2.0, gain = -2 to -5dB proportional to severity. If harshness is broadband (not peaked), use gentler cut across 3–6kHz with two PeakFilters. |
| **Risk of overprocessing** | HIGH. Cutting too much removes presence entirely. Vocal becomes distant, dull, lifeless. Never cut more than 5dB in a single PeakFilter. Always A/B match loudness. |

---

### 3.2 Sibilance

| Field | Value |
|---|---|
| **Audible symptom** | "S", "T", "F", "SH" sounds pierce through painfully. Listener flinches on consonants. Sounds like the mic is too close or the vocalist is too aggressive on consonants. |
| **Measurable signal feature** | Transient energy spikes in 5–8kHz band. High short-term RMS in sibilant band vs long-term RMS. Cepstral coefficients show sharp high-frequency transients. |
| **Likely frequency range** | 5–8kHz (varies by voice: female ~6–8kHz, male ~5–7kHz) |
| **Detection method** | **Librosa:** Compute onset strength envelope in 5–8kHz band using `librosa.onset.onset_strength` on a bandpass-filtered signal. Sibilance = high onset strength concentrated in sibilant band. Compare 5–8kHz onset density to 200Hz–4kHz onset density. Ratio > 2.0 = excessive sibilance. **TorchAudio:** `TorchaudioSpectralCentroid` on short frames — sibilant frames have centroid > 5kHz. |
| **DSP response** | **Pedalboard:** No built-in de-esser. Approximate with `PeakFilter` at detected sibilant frequency, narrow Q (3.0–5.0), moderate cut (-3 to -6dB). For true de-essing, recommend external VST3 via `pedalboard.load_plugin()` (e.g., FabFilter Pro-DS, Waves DeEsser). In Alpha, use dynamic approach: detect sibilant frames, apply cut only during those frames using time-varying gain. |
| **Risk of overprocessing** | VERY HIGH. Over-de-essing creates a lisp. Worse than the original problem. Never cut more than 6dB. Never use Q > 5.0 without listening. |

---

### 3.3 Muddiness

| Field | Value |
|---|---|
| **Audible symptom** | Vocals sound boomy, "closet recording," undefined. Words blur together. Low-end overwhelms clarity. Sounds like recording in an untreated small room. |
| **Measurable signal feature** | Excessive energy in 200–400Hz band relative to 1–4kHz band. Low spectral flatness in low-mids. High energy concentration below 500Hz. |
| **Likely frequency range** | 200–400Hz (primary mud), 80–200Hz (boominess) |
| **Detection method** | **Librosa:** Compute band energy ratio: energy(200–400Hz) / energy(1–4kHz). Ratio > 0.5 indicates mud. Use `librosa.feature.spectral_rolloff` — if rolloff frequency < 3kHz, vocal is low-heavy. **Essentia:** `BarkBands` — excessive energy in Bark bands 4–6 (200–400Hz). `LowLevelSpectralCentroid` skewed below 1.5kHz. |
| **DSP response** | **Pedalboard:** `PeakFilter` at 250–350Hz, wide Q (0.7–1.0), cut -2 to -4dB. If boominess detected (80–200Hz excess), add `LowShelfFilter` at 150Hz with -1 to -2dB. If mud is severe, combine both. |
| **Risk of overprocessing** | MEDIUM. Cutting too much makes vocal thin and bodiless. Never cut more than 6dB in the mud region. Always check that warmth (100–200Hz) is preserved. |

---

### 3.4 Boxiness

| Field | Value |
|---|---|
| **Audible symptom** | Vocal sounds like it is coming from a cardboard box or small room. Hollow, resonant quality. "Honky" character. Lacks openness. |
| **Measurable signal feature** | Narrow resonant peaks in 400–800Hz region. High spectral kurtosis in low-mids. Q-factor analysis shows narrow-band energy concentration. |
| **Likely frequency range** | 400–800Hz (boxiness), 300–500Hz (cardboard resonance) |
| **Detection method** | **Librosa:** Use `librosa.feature.spectral_contrast` — boxiness shows as a narrow peak in the 400–800Hz contrast band. Compute spectral kurtosis per frame; high kurtosis in 400–800Hz = narrow resonance = boxiness. **Essentia:** `SpectralPeaks` — detect dominant peaks in 400–800Hz. If a single peak dominates with > 6dB above neighbors = boxy resonance. |
| **DSP response** | **Pedalboard:** `PeakFilter` at detected resonance frequency, narrow Q (2.0–4.0), cut -2 to -4dB. Surgical cut — only remove the resonant peak, not the surrounding band. |
| **Risk of overprocessing** | LOW-MEDIUM. Surgical cuts are generally safe. Risk is cutting too broadly and removing vocal body. Keep Q narrow, gain moderate. |

---

### 3.5 Thinness

| Field | Value |
|---|---|
| **Audible symptom** | Vocal sounds like a headset mic or phone call. No body, no warmth, no chest resonance. Feels disconnected and weak. Lacks "expensive" quality. |
| **Measurable signal feature** | Low energy in 100–300Hz band relative to 1–4kHz band. Spectral centroid skewed high. Low energy below 500Hz. High spectral rolloff. |
| **Likely frequency range** | 100–300Hz (body), 80–150Hz (chest warmth) |
| **Detection method** | **Librosa:** Compute band energy ratio: energy(100–300Hz) / energy(1–4kHz). Ratio < 0.15 indicates thinness. `librosa.feature.spectral_centroid` — if mean centroid > 3kHz, vocal is bright/thin. **Essentia:** `LowLevelSpectralCentroid` > 2.5kHz = thin. `BarkBands` — low energy in bands 2–4 (100–300Hz). |
| **DSP response** | **Pedalboard:** `LowShelfFilter` at 200Hz, gain +1 to +3dB, Q 0.7. Gentle warmth boost. If vocal is also harsh, do NOT boost — first reduce harshness, then reassess thinness. Thinness + harshness = needs mid-range rebalancing, not simple boost. |
| **Risk of overprocessing** | MEDIUM. Boosting low-mids on a muddy vocal makes it worse. Always diagnose mud vs thinness together. If both mud and thinness are detected, the issue is likely uneven frequency response — cut mud, don't boost lows. |

---

### 3.6 Clipping

| Field | Value |
|---|---|
| **Audible symptom** | Harsh digital distortion on loud peaks. Crackling, breaking up on consonants and loud notes. Sounds like the recording level was set too hot. |
| **Measurable signal feature** | Samples at or near +/- 1.0 (digital full scale). High proportion of samples in top 1% of amplitude range. Flat-topped waveforms (zero-crossing analysis shows extended plateaus). |
| **Likely frequency range** | Broadband — affects entire signal, most audible in transients |
| **Detection method** | **Librosa/Numpy:** Count samples where |amplitude| > 0.99. If > 0.1% of total samples = clipping. Check for consecutive samples at same value (flat tops). **FFmpeg:** `astats` filter — check "Peak level dB" = 0.0dB and "Number of NaN/Inf samples." **Essentia:** `Loudness` and `Crest` — crest factor < 6dB with peak at 0dBFS = clipped. |
| **DSP response** | **Pedalboard:** First, apply `Gain` with negative dB to bring peaks below 0.99. Then use `Limiter` at -1dBFS as safety ceiling. If clipping is severe, recommend re-recording — DSP cannot restore lost information. For mild clipping, `Distortion` at very low drive (1–2dB) can mask artifacts through controlled saturation. |
| **Risk of overprocessing** | HIGH. Clipped audio has permanently lost information. No DSP can restore it. Only mitigate. Warn user if clipping is detected. |

---

### 3.7 Noise Floor

| Field | Value |
|---|---|
| **Audible symptom** | Constant hiss, hum, or room tone audible between vocal phrases. Computer fan, AC noise, mic self-noise. Distracting during quiet passages. |
| **Measurable signal feature** | Non-zero RMS energy during silent passages (between vocal onsets). High spectral flatness in silent regions. Consistent broadband energy floor. |
| **Likely frequency range** | Broadband (hiss), 50/60Hz + harmonics (hum), 1–4kHz (mic self-noise) |
| **Detection method** | **Librosa:** Use `librosa.effects.split` to detect silent regions (top_db parameter). Compute RMS energy of silent regions vs vocal regions. Noise floor = mean RMS of silent regions. If noise floor > -50dBFS = problematic. **FFmpeg:** `astats` filter — "Noise floor dB" descriptor. **Essentia:** `SilenceDetector` + `RMS` on silent segments. |
| **DSP response** | **Pedalboard:** `NoiseGate` with threshold set 6–10dB above detected noise floor. Gentle ratio (1.5:1–2:1). If hum detected (50/60Hz), add `PeakFilter` at hum frequency with narrow Q and deep cut. For broadband hiss, gentle `PeakFilter` cut at 8–12kHz if hiss is concentrated there. |
| **Risk of overprocessing** | MEDIUM. Aggressive gating removes breaths and quiet words. Never set gate threshold above -30dBFS. Preserve breaths — they are humanity. If noise floor > -40dBFS, recommend re-recording. |

---

### 3.8 Dynamic Inconsistency

| Field | Value |
|---|---|
| **Audible symptom** | Some words are much louder than others. Listener constantly adjusts volume. Quiet passages inaudible, loud passages painful. Performance feels uncontrolled. |
| **Measurable signal feature** | High dynamic range (difference between peak and RMS). Large variance in short-term RMS across the vocal. High crest factor (> 20dB). |
| **Likely frequency range** | Broadband — affects entire signal |
| **Detection method** | **Librosa:** Compute RMS energy in 100ms windows. Calculate coefficient of variation (std/mean) of RMS envelope. CV > 0.8 = highly inconsistent dynamics. **Essentia:** `DynamicCompressor` analysis — estimate required gain reduction. `Crest` descriptor — crest factor > 18dB = needs compression. `Loudness` — large short-term loudness variance. |
| **DSP response** | **Pedalboard:** `Compressor` with threshold set to catch peaks (not average level). Ratio 3:1–4:1 for moderate control. Attack 10–20ms (preserve transients). Release 40–80ms (recover between phrases). If dynamics are extremely inconsistent, recommend serial compression: fast compressor (6:1, 5ms attack) for peaks, then gentle compressor (2:1, 20ms attack) for glue. |
| **Risk of overprocessing** | HIGH. Over-compression kills emotion and performance dynamics. Never compress more than 6dB gain reduction from a single stage. Always A/B with matched loudness. If the performance is intentionally dynamic (e.g., whisper-to-scream), respect it. |

---

### 3.9 Dullness

| Field | Value |
|---|---|
| **Audible symptom** | Vocal sounds muffled, closed, lifeless. No sparkle, no air, no detail. Consonants are soft. Sounds like recording through a pillow or with a low-quality mic. |
| **Measurable signal feature** | Low energy above 5kHz. Spectral rolloff below 8kHz. Low spectral centroid. High energy concentration below 2kHz with rapid drop-off above. |
| **Likely frequency range** | 5–12kHz (clarity), 10–16kHz (air) |
| **Detection method** | **Librosa:** Compute band energy ratio: energy(5–12kHz) / energy(200Hz–4kHz). Ratio < 0.1 indicates dullness. `librosa.feature.spectral_rolloff` — if rolloff < 6kHz = dull. `librosa.feature.spectral_centroid` — mean centroid < 1.5kHz = dull. **Essentia:** `LowLevelSpectralCentroid` < 1.5kHz. `SpectralContrast` — low contrast in upper bands. |
| **DSP response** | **Pedalboard:** `HighShelfFilter` at 10kHz, gain +1 to +3dB, Q 0.7. Gentle air boost. If dullness is combined with harshness (paradoxical but common with cheap mics), first address harshness, then reassess. Never boost air on a noisy recording — it amplifies hiss. |
| **Risk of overprocessing** | MEDIUM. Boosting high frequencies amplifies noise, sibilance, and room artifacts. Always check noise floor before boosting air. If noise floor > -50dBFS, do NOT boost above 8kHz. |

---

### 3.10 Nasal Tone

| Field | Value |
|---|---|
| **Audible symptom** | Vocal sounds honky, whiny, "talking through nose." Annoying quality that makes listener want to turn it off. Common with cheap dynamic mics and poor mic technique. |
| **Measurable signal feature** | Resonant peak in 800Hz–1.5kHz region. Narrow-band energy concentration. High spectral kurtosis in upper low-mids. |
| **Likely frequency range** | 800Hz–1.5kHz (primary), 500–800Hz (secondary honk) |
| **Detection method** | **Librosa:** Use `librosa.feature.spectral_contrast` — detect peak in 800Hz–1.5kHz band. Compute spectral kurtosis per frame; high kurtosis in this range = nasal resonance. **Essentia:** `SpectralPeaks` — dominant peak in 800Hz–1.5kHz with > 4dB above neighbors. `BarkBands` — excessive energy in Bark band 9 (1kHz). |
| **DSP response** | **Pedalboard:** `PeakFilter` at detected nasal frequency, narrow Q (2.0–3.0), cut -2 to -4dB. Surgical cut — only remove the resonance, not the surrounding band. |
| **Risk of overprocessing** | LOW-MEDIUM. Nasal cuts are generally safe if surgical. Risk is cutting too broadly and removing vocal character. Some nasal quality is natural and genre-appropriate for rap. |

---

### 3.11 Poor Loudness

| Field | Value |
|---|---|
| **Audible symptom** | Vocal is too quiet compared to commercial references. Listener must turn up volume. Or vocal is too hot, causing listener fatigue. Does not compete with professional tracks. |
| **Measurable signal feature** | Integrated LUFS far from target (-16 to -14 LUFS for streaming, -9 to -7 LUFS for rap). Peak level too low or too high. RMS level inconsistent with genre norms. |
| **Likely frequency range** | Broadband — overall level issue |
| **Detection method** | **Librosa:** Compute RMS-based loudness estimate: 20 * log10(RMS). Compare to target -18dBFS (pre-compression) or -14dBFS (post-compression). **FFmpeg:** `loudnorm` filter — measures integrated LUFS, true peak, loudness range. **Essentia:** `Loudness` (EBU R128) — integrated LUFS, short-term LUFS, loudness range. |
| **DSP response** | **Pedalboard:** `Gain` adjustment to match target level. Use `Limiter` at -1dBFS as safety ceiling after gain adjustment. If loudness range is too high (> 15 LU), compression is needed first (see Dynamic Inconsistency). |
| **Risk of overprocessing** | LOW. Loudness matching is safe. Risk is pushing too hard and causing clipping — always use limiter after gain boost. |

---

### 3.12 Overcompressed Sound

| Field | Value |
|---|---|
| **Audible symptom** | Vocal sounds flat, lifeless, "squashed." No dynamics, no emotion, no punch. Every word is the same volume. Sounds like it went through a brick wall limiter. Common when artists over-process before sending to DrakoTune. |
| **Measurable signal feature** | Low crest factor (< 10dB). Low loudness range (< 5 LU). High RMS-to-peak ratio (> 0.7). Minimal variance in short-term RMS envelope. |
| **Likely frequency range** | Broadband — affects entire signal |
| **Detection method** | **Librosa:** Compute crest factor: peak / RMS. Crest factor < 10dB = overcompressed. Compute RMS envelope variance — low variance = overcompressed. **Essentia:** `Crest` descriptor < 10dB. `DynamicCompressor` — estimate that > 10dB of gain reduction was already applied. `Loudness` — loudness range < 5 LU. |
| **DSP response** | **Pedalboard:** Cannot "un-compress." Best approach: apply gentle `HighShelfFilter` (+1 to +2dB at 8kHz) to restore some perceived brightness. Use `Distortion` at very low drive (1–2dB) to add harmonic content that masks flatness. Recommend user provide less-processed source. In future, DrakoTune should detect overcompressed input and warn the user. |
| **Risk of overprocessing** | HIGH. Adding processing to an already overcompressed signal compounds the problem. Best response is often to process minimally and warn the user. |

---

### 3.13 Vocal Not Sitting Forward

| Field | Value |
|---|---|
| **Audible symptom** | Vocal sounds buried, distant, "behind the beat." Lacks presence and authority. Listener cannot focus on the vocal. Sounds like it was recorded in a large room with too much space. |
| **Measurable signal feature** | Low energy in 2–4kHz presence band relative to overall vocal energy. High energy in low-mids (200–500Hz) pushing vocal back. Low spectral centroid in presence region. |
| **Likely frequency range** | 2–4kHz (presence), 3–5kHz (forward placement) |
| **Detection method** | **Librosa:** Compute band energy ratio: energy(2–4kHz) / energy(200Hz–8kHz). Ratio < 0.15 = vocal lacks presence. `librosa.feature.spectral_centroid` — if centroid is below 2kHz, vocal is recessed. Compare presence band energy to commercial reference vocal. **Essentia:** `SpectralContrast` — low contrast in 2–4kHz band. `BarkBands` — low energy in Bark bands 15–17 (2–4kHz). |
| **DSP response** | **Pedalboard:** `PeakFilter` at 3–4kHz, wide Q (1.0–1.5), boost +1 to +3dB. If mud is also present, cut mud first (200–400Hz), then boost presence. Presence boost without mud cut = harsh and forward but still muddy. Presence boost on a thin vocal = harsh and thin. Always diagnose in context. |
| **Risk of overprocessing** | MEDIUM-HIGH. Boosting presence on a harsh vocal makes it unbearable. Always check harshness diagnosis before boosting presence. If both harshness and lack of presence are detected, the issue is uneven frequency response — cut harshness peaks, don't boost presence. |

---

## 4. Detection Pipeline Architecture

### 4.1 VocalProfile Dataclass

```python
from dataclasses import dataclass, field
from enum import Enum

class Severity(Enum):
    NONE = 0
    MILD = 1
    MODERATE = 2
    SEVERE = 3

@dataclass
class DiagnosisResult:
    category: str
    severity: Severity
    confidence: float  # 0.0–1.0
    detected_frequency_hz: float | None  # if applicable
    measured_value: float | None  # raw measurement
    threshold: float | None  # what triggered the diagnosis
    recommendation: str  # DSP action description

@dataclass
class VocalProfile:
    """Complete diagnostic report for a raw vocal file."""
    file_path: str
    sample_rate: int
    duration_seconds: float
    diagnoses: list[DiagnosisResult] = field(default_factory=list)
    overall_quality_score: float = 0.0  # 0–100, higher = better raw recording
    recommended_chain: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
```

### 4.2 Detection Flow

```
Input WAV (44100Hz, 16-bit, mono)
    │
    ▼
┌─────────────────────────────────┐
│  1. Global Analysis             │
│  - LUFS, crest factor, peak     │
│  - Duration, sample count       │
│  - Clipping detection           │
│  - Noise floor measurement      │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  2. Spectral Analysis           │
│  - Band energy ratios           │
│  - Spectral centroid, rolloff   │
│  - Spectral contrast            │
│  - Spectral kurtosis            │
│  - Bark band energy distribution│
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  3. Temporal Analysis           │
│  - RMS envelope variance        │
│  - Onset strength in sibilant   │
│  - Silent region detection      │
│  - Dynamic range measurement    │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  4. Diagnosis Engine            │
│  - Run all 13 category checks   │
│  - Cross-reference findings     │
│  - Resolve conflicts            │
│  - Build VocalProfile           │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  5. DSP Recommendation Engine   │
│  - Map diagnoses to DSP actions │
│  - Order actions correctly      │
│  - Set parameters by severity   │
│  - Build recommended chain      │
└─────────────────────────────────┘
    │
    ▼
VocalProfile + Recommended DSP Chain
```

### 4.3 Cross-Reference Rules

Diagnoses must be cross-referenced to avoid contradictory actions:

| Conflict | Resolution |
|---|---|
| Harshness + Dullness | Likely uneven response. Cut harshness peaks first, then reassess dullness. Do NOT boost air until harshness is resolved. |
| Mud + Thinness | Uneven response. Cut mud, do NOT boost lows. Reassess after mud cut. |
| Harshness + Vocal Not Forward | Cut harshness peaks, do NOT boost presence. Harshness cut often reveals natural presence. |
| Overcompressed + Any | Process minimally. Warn user. Cannot fix overcompression with more processing. |
| Noise Floor + Dullness | Do NOT boost air — it amplifies noise. Address noise floor first. |
| Clipping + Any | Warn user. Mitigate clipping first. Other diagnoses may be unreliable on clipped audio. |
| Sibilance + Harshness | Sibilance is transient, harshness is sustained. Treat separately: de-ess for sibilance, EQ cut for harshness. |

---

## 5. Recommended Changes to src/dsp/pipeline.py

### 5.1 New Module: src/dsp/diagnose.py

Create a new module that performs all 13 diagnostic checks and returns a `VocalProfile`.

```
src/dsp/
├── diagnose.py      # NEW — diagnostic analysis engine
├── pipeline.py      # MODIFIED — accepts VocalProfile, builds adaptive chain
├── preprocess.py    # unchanged
└── export.py        # unchanged
```

### 5.2 Modified pipeline.py

The `process_audio` function should accept an optional `VocalProfile`. If provided, it builds an adaptive chain based on the profile's recommendations. If not provided, it falls back to the current generic chain (backward compatible).

```python
def process_audio(
    input_path: str,
    output_path: str,
    profile: VocalProfile | None = None,
    params: CleanupParams | None = None,
) -> dict:
    if profile is not None:
        board = build_adaptive_chain(profile)
    else:
        board = build_cleanup_chain(params)
    # ... rest unchanged
```

### 5.3 build_adaptive_chain Function

This function reads the `VocalProfile` and constructs a Pedalboard chain that responds to the specific problems detected:

```python
def build_adaptive_chain(profile: VocalProfile) -> Pedalboard:
    """Build a DSP chain that responds to the vocal's specific problems."""
    plugins = []

    # Always start with gain staging
    loudness_diag = get_diagnosis(profile, "poor_loudness")
    if loudness_diag and loudness_diag.severity != Severity.NONE:
        plugins.append(Gain(gain_db=compute_gain_adjustment(loudness_diag)))

    # Highpass filter — always apply, but adjust cutoff based on mud/boxiness
    mud_diag = get_diagnosis(profile, "muddiness")
    hpf_cutoff = 80.0
    if mud_diag and mud_diag.severity >= Severity.MODERATE:
        hpf_cutoff = 100.0  # slightly more aggressive
    plugins.append(HighpassFilter(cutoff_frequency_hz=hpf_cutoff))

    # Mud cut — only if detected
    if mud_diag and mud_diag.severity >= Severity.MILD:
        plugins.append(PeakFilter(
            cutoff_frequency_hz=compute_mud_frequency(profile),
            gain_db=compute_mud_cut_gain(mud_diag),
            q=0.8,
        ))

    # Boxiness cut — only if detected
    boxy_diag = get_diagnosis(profile, "boxiness")
    if boxy_diag and boxy_diag.severity >= Severity.MILD:
        plugins.append(PeakFilter(
            cutoff_frequency_hz=boxy_diag.detected_frequency_hz,
            gain_db=compute_surgical_cut_gain(boxy_diag),
            q=3.0,
        ))

    # Nasal cut — only if detected
    nasal_diag = get_diagnosis(profile, "nasal_tone")
    if nasal_diag and nasal_diag.severity >= Severity.MILD:
        plugins.append(PeakFilter(
            cutoff_frequency_hz=nasal_diag.detected_frequency_hz,
            gain_db=compute_surgical_cut_gain(nasal_diag),
            q=2.5,
        ))

    # Harshness cut — only if detected (and not already overcompressed)
    harsh_diag = get_diagnosis(profile, "harshness")
    overcomp_diag = get_diagnosis(profile, "overcompressed")
    if harsh_diag and harsh_diag.severity >= Severity.MILD:
        if not overcomp_diag or overcomp_diag.severity < Severity.MODERATE:
            plugins.append(PeakFilter(
                cutoff_frequency_hz=compute_harshness_frequency(profile),
                gain_db=compute_harshness_cut_gain(harsh_diag),
                q=1.5,
            ))

    # Sibilance control — only if detected
    sib_diag = get_diagnosis(profile, "sibilance")
    if sib_diag and sib_diag.severity >= Severity.MILD:
        plugins.append(PeakFilter(
            cutoff_frequency_hz=sib_diag.detected_frequency_hz,
            gain_db=compute_sibilance_cut_gain(sib_diag),
            q=4.0,
        ))

    # Noise gate — only if noise floor is problematic
    noise_diag = get_diagnosis(profile, "noise_floor")
    if noise_diag and noise_diag.severity >= Severity.MILD:
        gate_threshold = compute_gate_threshold(noise_diag)
        plugins.append(NoiseGate(
            threshold_db=gate_threshold,
            ratio=1.5,
            attack_ms=1,
            release_ms=250,
        ))

    # Compression — only if dynamics are inconsistent
    dynamic_diag = get_diagnosis(profile, "dynamic_inconsistency")
    if dynamic_diag and dynamic_diag.severity >= Severity.MILD:
        plugins.append(Compressor(
            threshold_db=compute_compression_threshold(dynamic_diag),
            ratio=compute_compression_ratio(dynamic_diag),
            attack_ms=15,
            release_ms=60,
        ))

    # Presence boost — only if vocal lacks forward placement
    # AND harshness is not severe
    forward_diag = get_diagnosis(profile, "vocal_not_sitting_forward")
    if forward_diag and forward_diag.severity >= Severity.MILD:
        if not harsh_diag or harsh_diag.severity < Severity.MODERATE:
            plugins.append(PeakFilter(
                cutoff_frequency_hz=3500,
                gain_db=1.5,
                q=1.2,
            ))

    # Air boost — only if dull AND noise floor is acceptable
    dull_diag = get_diagnosis(profile, "dullness")
    if dull_diag and dull_diag.severity >= Severity.MILD:
        if not noise_diag or noise_diag.severity < Severity.MODERATE:
            plugins.append(HighShelfFilter(
                cutoff_frequency_hz=10000,
                gain_db=1.5,
                q=0.7,
            ))

    # Warmth boost — only if thin AND not muddy
    thin_diag = get_diagnosis(profile, "thinness")
    if thin_diag and thin_diag.severity >= Severity.MILD:
        if not mud_diag or mud_diag.severity < Severity.MODERATE:
            plugins.append(LowShelfFilter(
                cutoff_frequency_hz=200,
                gain_db=1.5,
                q=0.7,
            ))

    # Output limiter — always apply
    plugins.append(Limiter(threshold_db=-1, release_ms=100))

    return Pedalboard(plugins)
```

### 5.4 Modified run_alpha.py

The CLI should run diagnosis first, print the VocalProfile summary, then process:

```
DrakoTune Alpha 2 Pipeline
===========================
Input: Headlock (RawVocals).wav

[0/4] Diagnosing vocal problems...
      Harshness: MODERATE (peak at 3.8kHz)
      Muddiness: MILD (250–350Hz excess)
      Sibilance: MODERATE (6.2kHz)
      Dynamic inconsistency: MILD
      Noise floor: MILD (-45dBFS)
      Overall quality: 62/100

[1/4] Building adaptive DSP chain...
      8 plugins selected based on diagnosis

[2/4] Preprocessing with FFmpeg...
      Normalized to 44100Hz, 16-bit, mono

[3/4] Applying adaptive DSP chain...
      Processed 162.0s of audio
      Chain: HPF(100Hz) → mud cut → harshness cut → sibilance cut → gate → comp → presence → limiter

[4/4] Exporting before/after files...

Done in 0.8s
Before: output/headlock_before.wav
After:  output/headlock_after.wav
```

---

## 6. Milestone Alpha 2: Diagnostic Audio Intelligence Layer

### The Question

> "Can DrakoTune diagnose what is wrong with a raw vocal and apply targeted DSP that makes a clearly audible improvement?"

### Scope

1. Create `src/dsp/diagnose.py` — diagnostic analysis engine with all 13 categories
2. Implement detection methods using Librosa (primary) and Essentia (secondary)
3. Create `VocalProfile` dataclass and diagnosis engine
4. Modify `src/dsp/pipeline.py` to accept `VocalProfile` and build adaptive chains
5. Modify `scripts/run_alpha.py` to run diagnosis first, then adaptive processing
6. Write tests for diagnosis engine (synthetic audio with known problems)
7. Re-run real vocal test (Headlock) with adaptive pipeline
8. Compare before/after: generic chain vs adaptive chain

### Deliverables

- [ ] `src/dsp/diagnose.py` — diagnostic analysis engine
- [ ] `src/dsp/pipeline.py` — modified for adaptive chains
- [ ] `scripts/run_alpha.py` — modified for diagnosis-first workflow
- [ ] `tests/test_diagnose.py` — diagnosis engine tests (synthetic audio)
- [ ] `docs/06-alpha-diagnosis-plan.md` — this document
- [ ] Updated `CURRENT_MILESTONE.md`

### Acceptance Criteria

- [ ] Diagnosis engine detects all 13 categories on synthetic test audio
- [ ] Adaptive chain produces audibly different output from generic chain on real vocal
- [ ] Diagnosis report is human-readable and explains what was found
- [ ] Cross-reference rules prevent contradictory DSP actions
- [ ] Processing time under 60s for 3-minute vocal (diagnosis + processing)
- [ ] Tests pass with pytest
- [ ] No fake DSP — all analysis uses real Librosa/Essentia functions

### NOT in Scope

- Frontend, backend, auth, UI, database, deployment
- VST3 plugin loading (future milestone)
- Dynamic/time-varying DSP (future milestone)
- Demucs vocal isolation (future milestone)
- Conversational AI layer (future milestone)
- Beta app features

### Timeline

Estimated: 2–3 focused sessions

---

## 7. How DrakoTune Should Eventually Guide Premium Plugin Workflows

DrakoTune's long-term vision is not to replace professional tools — it is to make them accessible to underground artists who own them but do not know how to use them effectively.

### The Problem

Many underground artists own:
- **FL Studio** (DAW with stock plugins)
- **Auto-Tune** (pitch correction)
- **FabFilter Pro-Q 3** (surgical EQ)
- **FabFilter Pro-C 2** (compressor)
- **FabFilter Pro-DS** (de-esser)
- **Waves SSL Compressor, CLA Vocals, RVox**
- **Soundtoys Decapitator** (saturation)
- **iZotope Nectar, RX** (vocal suite)
- Various free VSTs

But they do not know:
- What order to put plugins in
- What frequencies to cut or boost
- What compressor settings to use
- Whether their vocal needs de-essing or saturation
- How to avoid overprocessing

### DrakoTune as a Diagnostic Guide

The diagnosis engine (Alpha 2) should eventually produce two outputs:

**Output A: Automated DSP Chain**
The system processes the audio directly using Pedalboard (what Alpha 2 does).

**Output B: Plugin Recipe for the User's Tools**
The system tells the user exactly what to do with the plugins they already own:

```
DrakoTune Diagnosis Report for "Headlock (RawVocals).wav"
==========================================================

Your vocal has these problems:
1. Harshness at 3.8kHz (MODERATE)
2. Sibilance at 6.2kHz (MODERATE)
3. Muddiness at 250–350Hz (MILD)
4. Dynamic inconsistency (MILD)
5. Noise floor at -45dBFS (MILD)

Recommended chain in FL Studio:
───────────────────────────────

1. Fruity Parametric EQ 2
   - Cut at 300Hz, -3dB, Q=0.8 (removes mud)
   - Cut at 3.8kHz, -4dB, Q=1.5 (reduces harshness)
   - Cut at 6.2kHz, -3dB, Q=4.0 (sibilance control)

2. Fruity Compressor
   - Threshold: -18dB, Ratio: 3.5:1
   - Attack: 15ms, Release: 60ms
   - Makeup gain: +2dB

3. Fruity Limiter (Gate mode)
   - Threshold: -40dB, Ratio: 1.5:1
   - Release: 250ms

4. Fruity Limiter (Comp mode)
   - Ceiling: -1dB (output protection)

If you have FabFilter Pro-Q 3:
   Use the same EQ settings above — Pro-Q 3's dynamic
   EQ mode is better for the sibilance cut. Set 6.2kHz
   cut to DYNAMIC mode, sidechain the vocal to itself.

If you have FabFilter Pro-DS:
   Use it instead of the static 6.2kHz EQ cut.
   Range: 5–8kHz, Threshold: -20dB, Ratio: 3:1.

If you have Auto-Tune:
   Apply AFTER the EQ and compression chain above.
   Retune speed: 15–20ms for natural rap correction.
   Do NOT apply Auto-Tune before EQ — it will track
   poorly on muddy, harsh audio.

Warning:
   Your noise floor is -45dBFS. Consider recording in
   a quieter environment. Do not gate above -35dBFS
   or you will lose breaths and quiet words.
```

### Implementation Phases

| Phase | Capability | Milestone |
|---|---|---|
| Alpha 2 | Diagnose problems, apply adaptive DSP via Pedalboard | Current plan |
| Beta 1 | Generate plugin recipes for FL Studio stock plugins | Beta |
| Beta 2 | Generate recipes for FabFilter, Waves, Soundtoys | Beta |
| Beta 3 | Load VST3 plugins directly via Pedalboard `load_plugin()` | Beta |
| Gamma 1 | Auto-Tune integration guidance (pre/post processing order) | Gamma |
| Gamma 2 | Real-time plugin parameter suggestions during FL Studio session | Gamma |

### Key Principle

DrakoTune should never say "buy this plugin." It should say "here is what to do with what you already have." The diagnosis is the product — the DSP execution is a bonus.

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Librosa analysis is too slow for long vocals | HIGH | Analyze in chunks (30s windows), aggregate results. Use numpy vectorized operations. |
| False positive diagnoses lead to wrong DSP | HIGH | Use conservative thresholds. Require multiple detection methods to agree. Always allow manual override. |
| Cross-reference rules are too complex | MEDIUM | Start with simple rules (6 conflicts). Expand based on real vocal testing. |
| User provides already-processed vocal | MEDIUM | Detect overcompression and warn. Process minimally. |
| Synthetic test audio does not match real vocals | MEDIUM | Test with multiple real vocal files of different genres, mics, and recording conditions. |
| Diagnosis adds significant processing time | LOW | Diagnosis is analysis-only, no audio I/O. Should complete in < 10s for 3-minute vocal. |

---

## 9. Success Metrics for Alpha 2

1. **Audible difference**: When playing before/after of Headlock with adaptive chain, at least 2 listeners independently say "the after is clearly better."
2. **Diagnosis accuracy**: On synthetic test audio with known problems, diagnosis engine correctly identifies all injected problems with > 80% accuracy.
3. **Processing time**: Full diagnosis + adaptive processing completes in < 60s for 3-minute vocal.
4. **No regression**: Adaptive chain never produces worse output than generic chain on any test vocal.
5. **Human-readable report**: Diagnosis output is understandable by a non-engineer artist.

---

## 10. Next Actions

1. **Create `src/dsp/diagnose.py`** — Implement all 13 diagnostic checks using Librosa
2. **Create `tests/test_diagnose.py`** — Synthetic audio tests with known problems
3. **Modify `src/dsp/pipeline.py`** — Add `build_adaptive_chain` and `VocalProfile` support
4. **Modify `scripts/run_alpha.py`** — Add diagnosis-first workflow
5. **Re-run Headlock test** — Compare generic vs adaptive chain
6. **Update `CURRENT_MILESTONE.md`** — Reflect Alpha 2 scope
7. **Listen and validate** — Human ear test is the final gate
