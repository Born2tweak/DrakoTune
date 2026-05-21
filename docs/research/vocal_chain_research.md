# DrakoTune Vocal Chain Research

> DSP Research for Milestone Alpha and beyond.
> Goal: Make raw underground vocals sound smoother, more expensive, more alive, and professionally listenable — without destroying humanity.

---

## 1. Professional Vocal Chain Order

The signal flow order matters enormously. Processing in the wrong order creates compounding problems. The industry-standard vocal chain for rap/hip-hop is:

### Recommended Chain Order

```
1. Gain Staging        → Normalize input level
2. Highpass Filter     → Remove sub-bass rumble
3. Subtractive EQ      → Cut problem frequencies (mud, nasal, harshness)
4. Compression (A)     → Tame peaks, control dynamics
5. De-essing           → Reduce sibilance (after compression, critical)
6. Additive EQ         → Boost presence, add air
7. Compression (B)     → Gentle glue compression (serial compression)
8. Saturation          → Harmonic warmth, density
9. Reverb/Delay        → Spatial depth, atmosphere (send/return preferred)
10. Limiter            → Final peak protection
```

### Why This Order

- **Subtractive EQ before compression**: Prevents the compressor from reacting to problem frequencies (mud, rumble). If you compress first, the compressor pumps on frequencies you'd have cut anyway.
- **De-esser after compression**: Compression raises sibilance levels. If you de-ess first, the compressor brings the sibilance right back up.
- **Additive EQ after compression**: Presence and air boosts don't get squashed by gain reduction.
- **Saturation after EQ/compression**: Adds harmonics to a clean, balanced signal rather than amplifying problems.
- **Limiter last**: Final safety net, catches any peaks created by previous processing.

### DrakoTune Alpha Simplified Chain

For Milestone Alpha (Cleanup stage only), use a simplified chain:

```
1. Gain staging (normalize to -18dBFS peak)
2. Highpass filter (~80Hz)
3. Subtractive EQ (cut mud, cut harshness)
4. Compression (gentle, single stage)
5. Noise gate (light, between phrases)
6. Output gain normalization
```

---

## 2. EQ Frequency Guide for Vocals

### Frequency Map

| Range | Name | Character | Action |
|-------|------|-----------|--------|
| 20-80 Hz | Sub-bass / Rumble | Floor vibration, mic handling, air conditioning | **CUT** — Highpass filter. Always remove. No useful vocal content here. |
| 80-200 Hz | Low-end / Body | Chest resonance, warmth, proximity effect | **Careful** — Slight cut if boomy. Don't remove entirely or vocals sound thin. |
| 200-400 Hz | Mud zone | Boominess, boxiness, "cheap closet sound" | **CUT 2-4dB** — The #1 problem area for bedroom recordings. Wide Q cut around 250-350Hz cleans up most mud. |
| 400-800 Hz | Low-mids | Honkiness, hollowness, cardboard quality | **Surgical cut if needed** — Not always a problem. Only cut if you hear nasal or honky quality. |
| 800 Hz-1.5 kHz | Upper low-mids | Nasal, telephone-like quality | **Cut 1-3dB if nasal** — Common problem with cheap mics. Narrow Q cut. |
| 2-4 kHz | Presence | Vocal clarity, intelligibility, forward placement | **Boost 1-3dB** — This is what makes vocals "cut through." But too much = harsh and fatiguing. |
| 3-6 kHz | Harshness zone | Ear fatigue, shrillness, aggression | **CUT 2-4dB** — The primary harshness region. This is what makes cheap vocals painful to listen to. |
| 5-8 kHz | Sibilance | "S", "T", "F" sounds, brightness | **De-ess or cut** — Sibilance lives here. Use a de-esser (dynamic EQ) rather than static cuts to preserve brightness in non-sibilant moments. |
| 8-12 kHz | Brilliance | Clarity, detail, consonant definition | **Gentle boost if needed** — Can add sparkle but easily overcooked. |
| 12-20 kHz | Air | Breathiness, openness, "expensive" sheen | **Shelf boost 1-3dB** — The "expensive sound" frequency. A subtle high shelf here makes vocals sound polished and airy without harshness. |

### The Three Essential EQ Moves

These three moves handle 90% of vocal EQ situations:

1. **Mud cut**: -2 to -4dB around 250-350Hz, wide Q (0.7-1.0)
2. **Presence boost**: +1 to +3dB around 3-4kHz, wide Q (1.0-1.5) — OR harshness cut in the same zone
3. **Air shelf**: +1 to +3dB high shelf at 10-12kHz

### Underground Rap Specific

- Underground/rage vocals often benefit from LESS air boost and MORE mid-presence
- Intentional grit in the 2-4kHz range is sometimes desirable — don't over-cut
- Dark/atmospheric vocals: reduce air shelf, boost low-mids slightly
- Aggressive vocals: allow more 3-5kHz energy, use saturation instead of EQ for edge

---

## 3. Harshness in Underground Rap Vocals

### What Causes Harshness

1. **Cheap microphones** that accentuate 2-8kHz
2. **Untreated rooms** creating comb filtering and early reflections
3. **Proximity effect** from recording too close (boomy + harsh simultaneous)
4. **Clipping / digital distortion** from hot input levels
5. **Aggressive delivery** — rap vocals naturally have more transient energy
6. **SM58-style mics** with presence peaks baked in

### Primary Harshness Frequencies

| Frequency | Type of Harshness |
|-----------|-------------------|
| 2.5-3.5 kHz | "Ice pick" — ear-piercing, fatiguing presence |
| 3-5 kHz | "Cheap/thin" — makes vocals sound amateur |
| 4-6 kHz | "Nasal harshness" — whiny, metallic quality |
| 5-8 kHz | Sibilance — "S" and "T" sounds cutting through painfully |
| 6-10 kHz | "Digital harshness" — the "recorded in a bedroom" sound |

### De-essing Strategy

- **Target range**: 5-8kHz (adjust per voice)
- **Approach**: Dynamic EQ or sidechain compression on the sibilant band
- **Pedalboard limitation**: No built-in de-esser. Implement as a PeakFilter with narrow Q targeting the sibilant frequency. For Alpha, a gentle static cut at 6-7kHz is acceptable.
- **Amount**: Aim for 3-6dB of reduction on sibilant peaks only
- **Warning**: Over-de-essing creates a lisp effect. Worse than sibilance.

---

## 4. Compression for Natural But Polished Vocals

### Core Philosophy

Rap vocals need MORE compression than most genres — the delivery is dynamic and percussive. But over-compression kills emotion. The goal is "consistent but alive."

### Single Compressor Settings (Alpha)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Threshold** | -18 to -24 dB | Catch peaks without crushing quiet moments |
| **Ratio** | 3:1 to 4:1 | Moderate control. 4:1 is the sweet spot for most rap vocals. |
| **Attack** | 10-20 ms | Fast enough to catch peaks, slow enough to preserve transient punch. Too fast (< 5ms) kills consonant clarity. |
| **Release** | 40-80 ms | Medium-fast. Lets compressor recover between words. Too slow = pumping. Too fast = distortion. |
| **Gain reduction** | 2-4 dB on peaks | Never more than 6dB from a single compressor stage |
| **Makeup gain** | Compensate for reduction | Match perceived loudness to bypass |

### Serial Compression (Future Stages)

For later processing stages (Presence/Polish), use two compressors:

**Compressor A — Peak Taming:**
- Ratio: 6:1 to 8:1
- Attack: 1-5ms (fast, catches peaks)
- Threshold: high (only catches loudest moments)
- Gain reduction: 3-7dB on peaks only

**Compressor B — Glue:**
- Ratio: 2:1 to 3:1
- Attack: 15-30ms (slower, musical)
- Threshold: lower (gentle, consistent compression)
- Gain reduction: 2-4dB steady

### What NOT to Do

- **Never compress more than 6dB** with a single compressor instance
- **Never use ratio > 8:1** on vocals (that's limiting, not compressing)
- **Never use attack < 1ms** — kills all transient life
- **Never set release to auto** without testing — auto-release on some implementations pumps badly
- **Never compress without gain staging first** — garbage in, garbage out

---

## 5. Saturation Approaches

### Why Saturation Matters for Underground Vocals

Saturation adds harmonic content that makes thin digital recordings sound fuller and more analog. It's the difference between "recorded in GarageBand" and "recorded on expensive gear."

### Types of Saturation

| Type | Character | Use Case |
|------|-----------|----------|
| **Tape** | Warm, smooth, rounds transients, slight compression | Best for general vocal warming. Safe default. |
| **Tube** | Rich, dense, even harmonics (2nd, 4th) | Best for adding body and warmth without edge. |
| **Transistor** | Gritty, edgy, odd harmonics (3rd, 5th) | Good for aggressive/rage vocals. |
| **Clipping** | Hard, aggressive, digital edge | For intentional distortion effects only. |

### Saturation in Pedalboard

Pedalboard provides:
- `Distortion(drive_db=...)` — general waveshaping distortion
- `Clipping()` — hard clipping

For subtle tape/tube saturation, Pedalboard's `Distortion` at very low drive values (1-5dB) approximates soft clipping. For higher quality saturation, load a VST3 plugin via `pedalboard.load_plugin()`.

### Saturation Guidelines

| Context | Drive Amount | Notes |
|---------|-------------|-------|
| Subtle warmth | 1-3 dB | You should FEEL it more than hear it. 1-2% THD. |
| Vocal density | 3-6 dB | Audible warmth. Fills out thin vocals. |
| Underground grit | 6-12 dB | Intentional coloring. Must be genre-appropriate. |
| Aggressive/rage | 12+ dB | Heavy distortion. Genre-specific aesthetic choice. |

### Critical Rule

> Saturation should be applied AFTER EQ and compression. Saturating a muddy signal amplifies the mud. Saturating a clean, balanced signal adds warmth.

### What NOT to Do

- Never apply heavy saturation to un-EQ'd vocals
- Never saturate sibilant frequencies (causes metallic artifacts)
- Never use Pedalboard's `Distortion` above 10dB for "warmth" — it's not a tape emulator at high settings
- Consider: high-shelf cut BEFORE saturation to protect high frequencies from harsh harmonics

---

## 6. Stereo Considerations

### Lead Vocal Placement

**Lead vocals in rap should be MONO and CENTER.** This is non-negotiable for the genre.

- Lead vocal: dead center, mono
- Doubles/ad-libs: panned slightly (20-40%) or widened
- Reverb/delay returns: can be stereo to create width around a centered vocal
- Beat elements: occupy the sides, creating space for the centered vocal

### Stereo Processing for Vocals

For Alpha (mono cleanup), stereo is not relevant. For future stages (Blend):

- **Reverb**: Apply in stereo on a send/return bus — creates width without moving the vocal
- **Delay**: Stereo ping-pong delay creates width. Use sparingly in underground rap.
- **Mid-Side EQ**: Cut upper-mids (3-6kHz) in the mid channel of the beat to create a "pocket" for the vocal

### What NOT to Do

- Never apply stereo widening to a lead rap vocal
- Never hard-pan a lead vocal
- Never use chorus on a lead rap vocal (destroys clarity and mono compatibility)

---

## 7. Noise Reduction Strategies

### The Problem

Bedroom recordings have:
- Room tone / ambient noise (AC, fans, computer)
- Mic self-noise (cheap condenser hiss)
- Floor vibration / rumble
- Mouth clicks / pops
- Background noise from walls / reflections

### Strategy: Layered Noise Reduction

| Layer | Tool | Settings | Purpose |
|-------|------|----------|---------|
| 1. Highpass filter | `HighpassFilter(cutoff_frequency_hz=80)` | 80Hz, 12dB/oct | Remove rumble, floor vibration |
| 2. Noise gate | `NoiseGate(threshold_db=-40, ratio=1.5, release_ms=250)` | Gentle settings | Reduce noise between phrases |
| 3. Gentle EQ | `PeakFilter(cutoff_frequency_hz=..., gain_db=-2, q=2.0)` | Targeted narrow cuts | Remove specific hum frequencies (50/60Hz harmonics) |

### Noise Gate Best Practices

- **Threshold**: Set just above the noise floor. Too high = cuts off quiet words and breaths.
- **Ratio**: 1.5:1 to 2:1 for gentle gating (attenuation, not silence). Hard gates (10:1+) sound unnatural.
- **Attack**: < 1ms (must open instantly when voice starts)
- **Release**: 200-500ms (must fade smoothly, not chop)
- **Hold**: If available, 50-100ms (prevents fluttering on quiet passages)

### Critical Rule

> Noise reduction of more than 3-6dB introduces audible artifacts. If the recording needs more than 6dB of noise reduction, the recording itself is the problem. DrakoTune should reduce noise gently, not attempt heroic restoration.

### What NOT to Do

- Never gate so aggressively that breaths are removed (breaths = humanity)
- Never use spectral denoise without user confirmation (can destroy vocal texture)
- Never assume noise = bad (room tone at low levels is natural and adds presence)

---

## 8. Common Mistakes in AI Vocal Enhancers

### Why Most AI Tools Fail Underground Artists

1. **Over-cleaning**: Aggressive noise removal strips texture, breath, and grit — the exact things that make underground vocals feel authentic.

2. **Generic presets**: "Auto" presets optimize for podcasts and pop vocals, not underground rap. They normalize toward a "safe" sound that misses the aesthetic.

3. **Treating sibilance as noise**: AI algorithms often misinterpret breath, sibilance, and vocal inflections as noise, creating robotic artifacts.

4. **Invisible over-compression**: AI enhancers often compress 10-15dB without the user realizing, producing flat, lifeless output.

5. **Targeting loudness over emotion**: Optimizing for LUFS/RMS loudness metrics rather than perceived quality and emotional impact.

6. **One-pass processing**: Applying a single massive processing step instead of incremental, stage-based refinement. Users can't understand or control what happened.

7. **Ignoring genre context**: "Clean" is the wrong target for underground music. Controlled dirt, saturation, and texture are features, not bugs.

8. **Gating artifacts**: Aggressive noise gates that engage/disengage inconsistently during quiet moments, creating an unnatural "pumping" or "breathing" effect.

9. **Frequency masking ignorance**: Not considering how the vocal interacts with the beat. Processing vocals in isolation, then they don't blend when combined.

### How DrakoTune Must Differ

- **Preserve humanity**: Always err on the side of under-processing
- **Stage-based transparency**: Users see and control each processing step
- **Genre-aware defaults**: Default presets tuned for underground aesthetics, not pop/podcast
- **Emotional validation**: "Does this sound alive?" not "Is this technically clean?"

---

## 9. What Makes Vocals Sound "Cheap"

### Technical Indicators

1. **Excessive mud** (200-400Hz buildup) — "closet sound"
2. **Harshness** (3-6kHz resonance peaks) — painful to listen to
3. **Sibilance** (5-8kHz uncontrolled) — "ssss" sounds cut through
4. **Thin body** (lack of 100-200Hz warmth) — "headset mic" quality
5. **No air** (missing 10kHz+ content) — closed, dull, flat
6. **Inconsistent dynamics** — some words way louder than others
7. **Room reverb baked in** — "bathroom recording" quality
8. **Digital clipping** — harsh distortion on peaks
9. **Background noise** — constant hiss or hum
10. **No depth** — vocal sits ON TOP of the beat rather than IN the beat

### Emotional Indicators

- Vocals feel "disconnected" from the music
- Listening fatigue within 30 seconds
- No sense of space or atmosphere
- The voice sounds like a different "world" than the beat
- Flat, lifeless delivery (even if the performance was great)

---

## 10. What Makes Vocals Sound "Expensive"

### Technical Indicators

1. **Clean low-end** — no rumble, no mud, warmth without boominess
2. **Smooth presence** — clear without harsh, forward without fatiguing
3. **Controlled sibilance** — bright but not piercing
4. **Consistent dynamics** — even volume, every word audible
5. **Air and shimmer** — subtle high-frequency sheen
6. **Depth** — vocal sits IN the mix with spatial context
7. **Warmth** — subtle harmonic saturation, analog feel
8. **Low noise floor** — clean silence between phrases
9. **Cohesion with beat** — sounds like one unified production
10. **Loudness without clipping** — competitively loud but clean

### Emotional Indicators

- You can listen for minutes without fatigue
- The voice feels "present" — like the artist is in the room
- Atmosphere and mood are enhanced, not stripped
- Confidence and authority in the sound
- The listener focuses on the PERFORMANCE, not the recording quality

---

## 11. Pedalboard Plugin Reference (for Implementation)

### Available Plugins and Parameters

```python
# === FILTERS ===

HighpassFilter(cutoff_frequency_hz=80)
# Removes everything below cutoff. Use 80Hz for rumble removal.

LowpassFilter(cutoff_frequency_hz=15000)
# Removes everything above cutoff. Rarely needed on vocals.

PeakFilter(cutoff_frequency_hz=3000, gain_db=-3, q=1.0)
# Parametric EQ bell. The workhorse for surgical cuts and boosts.
# cutoff_frequency_hz: center frequency
# gain_db: boost (+) or cut (-), range roughly -24 to +24
# q: bandwidth (0.5 = wide, 4.0 = narrow, 1.0 = moderate)

LowShelfFilter(cutoff_frequency_hz=250, gain_db=-2, q=0.7)
# Shelf EQ affecting everything below cutoff.

HighShelfFilter(cutoff_frequency_hz=10000, gain_db=2, q=0.7)
# Shelf EQ affecting everything above cutoff. Use for "air" boost.

# === DYNAMICS ===

Compressor(threshold_db=-20, ratio=4, attack_ms=15, release_ms=60)
# threshold_db: level above which compression engages
# ratio: compression ratio (1 = none, inf = limiter)
# attack_ms: how fast compression engages
# release_ms: how fast compression releases

NoiseGate(threshold_db=-40, ratio=1.5, attack_ms=1, release_ms=250)
# threshold_db: below this level, signal is attenuated
# ratio: how much to attenuate (1.5 = gentle, 10+ = hard gate)
# attack_ms: how fast gate opens (keep < 1ms)
# release_ms: how fast gate closes (200-500ms for natural fade)

Limiter(threshold_db=-1, release_ms=100)
# Hard ceiling. Prevents any signal from exceeding threshold.

Gain(gain_db=0)
# Simple volume adjustment in dB.

# === EFFECTS ===

Distortion(drive_db=5)
# Waveshaping distortion. At low values (1-5dB) = subtle saturation.
# At high values (20+dB) = aggressive distortion.

Clipping()
# Hard clipping. Aggressive. Use only for intentional distortion.

Reverb(room_size=0.3, damping=0.5, wet_level=0.15, dry_level=0.85, width=1.0)
# room_size: 0.0 (small) to 1.0 (large)
# damping: high-frequency absorption (0=bright, 1=dark)
# wet_level: reverb signal level
# dry_level: dry signal level
# width: stereo spread

Delay(delay_seconds=0.3, feedback=0.3, mix=0.2)
# delay_seconds: delay time
# feedback: echo repetition (0=single, 1=infinite)
# mix: wet/dry balance

Chorus(rate_hz=1.0, depth=0.25, centre_delay_ms=7.0, feedback=0.0, mix=0.5)
# Generally NOT recommended for lead rap vocals.

# === UTILITY ===

Invert()
# Phase inversion. Niche use only.

Bitcrush(bit_depth=16)
# Bit depth reduction. Lo-fi effect.

Resample(target_sample_rate=22050)
# Sample rate reduction. Lo-fi effect.
```

---

## 12. DrakoTune Alpha — Recommended Chain

### The Alpha Cleanup Chain

This is the minimum viable chain for Milestone Alpha. It answers: "Can we make bad vocals noticeably better?"

```python
from pedalboard import Pedalboard, Gain, HighpassFilter, PeakFilter, \
    LowShelfFilter, HighShelfFilter, Compressor, NoiseGate, Limiter

alpha_cleanup_chain = Pedalboard([
    # 1. Input gain staging (normalize to -18dBFS via preprocessing)
    Gain(gain_db=0),  # Adjusted per-file after analysis

    # 2. Rumble removal
    HighpassFilter(cutoff_frequency_hz=80),

    # 3. Mud reduction (the #1 bedroom recording problem)
    PeakFilter(cutoff_frequency_hz=300, gain_db=-3, q=0.8),

    # 4. Harshness reduction (the #2 problem)
    PeakFilter(cutoff_frequency_hz=4000, gain_db=-2.5, q=1.0),

    # 5. Sibilance reduction (gentle static cut as de-esser substitute)
    PeakFilter(cutoff_frequency_hz=6500, gain_db=-2, q=2.0),

    # 6. Noise gate (reduce noise between phrases)
    NoiseGate(threshold_db=-40, ratio=1.5, attack_ms=1, release_ms=250),

    # 7. Compression (smooth dynamics)
    Compressor(threshold_db=-20, ratio=3.5, attack_ms=15, release_ms=60),

    # 8. Output normalization / peak protection
    Limiter(threshold_db=-1, release_ms=100),
])
```

### Parameter Adjustment Ranges (for future sliders)

| Parameter | Min | Default | Max | User-Facing Name |
|-----------|-----|---------|-----|------------------|
| HPF cutoff | 40 Hz | 80 Hz | 150 Hz | "Rumble removal" |
| Mud cut gain | 0 dB | -3 dB | -6 dB | "Mud reduction" |
| Mud cut freq | 200 Hz | 300 Hz | 450 Hz | — |
| Harshness cut gain | 0 dB | -2.5 dB | -6 dB | "Harshness reduction" |
| Harshness cut freq | 2.5 kHz | 4 kHz | 6 kHz | — |
| Sibilance cut gain | 0 dB | -2 dB | -5 dB | "Sibilance control" |
| Gate threshold | -60 dB | -40 dB | -25 dB | "Noise gate" |
| Comp threshold | -30 dB | -20 dB | -10 dB | "Compression" |
| Comp ratio | 2:1 | 3.5:1 | 6:1 | — |
| Comp attack | 5 ms | 15 ms | 30 ms | — |
| Comp release | 30 ms | 60 ms | 120 ms | — |
| Limiter threshold | -3 dB | -1 dB | -0.3 dB | "Output ceiling" |

---

## 13. Full 5-Stage Chain Preview (Future Roadmap)

### Stage 1: Cleanup (Alpha)
HPF → Mud EQ cut → Harshness EQ cut → Sibilance cut → Noise gate → Gentle compression → Limiter

### Stage 2: Presence
Serial compression (peak tamer + glue) → Presence boost (3-4kHz) → Air shelf (10kHz+) → Warmth shelf (100-200Hz, subtle)

### Stage 3: Blend
Reverb (room_size 0.2-0.5, wet 10-20%) → Delay (slapback 50-120ms, subtle) → Stereo width on FX returns only

### Stage 4: Emotion
Saturation (Distortion at 2-6dB drive) → Texture shaping (genre-specific EQ curves) → Controlled mid-range coloring

### Stage 5: Final Polish
Final limiter (-0.3 to -1 dBFS) → Output gain → Level matching to commercial references

---

## 14. Things That Must NEVER Be Overprocessed

| Processing | Danger Zone | Why |
|------------|-------------|-----|
| **Noise gate** | Threshold above -30dB | Cuts off breaths, quiet words, vocal tails. Destroys humanity. |
| **Compression** | > 6dB gain reduction per stage | Squashes dynamics, creates flat lifeless vocal. |
| **De-essing / sibilance cut** | > 6dB cut | Creates a lisp. Worse than the original sibilance. |
| **Mud EQ cut** | > 6dB cut at 200-400Hz | Makes vocals thin, hollow, and bodiless. |
| **Air boost** | > 4dB shelf above 10kHz | Creates hiss, emphasizes room noise, sounds brittle. |
| **Harshness cut** | > 5dB cut at 3-6kHz | Removes presence entirely. Vocal sounds distant and dull. |
| **Saturation** | > 10dB drive for "warmth" | Becomes distortion, not warmth. Destroys clarity. |
| **Reverb wet level** | > 30% wet | Vocal disappears into reverb wash. Loses intimacy. |

### The DrakoTune Golden Rule

> When in doubt, process LESS. An under-processed vocal that sounds natural is always better than an over-processed vocal that sounds robotic. The artist's humanity is the product — protect it at all costs.

---

## Sources

- [Best Vocal Chain Order 2026 — Rys Up Audio](https://rysupaudio.com/blogs/news/best-vocal-chain-order)
- [How to Mix Hip-Hop Vocals — Rys Up Audio](https://rysupaudio.com/blogs/news/how-to-mix-hip-hop-vocals)
- [Vocal EQ Chart — Unison Audio](https://unison.audio/eq-chart/)
- [How to Compress Rap Vocals — Cryo Mix](https://cryo-mix.com/blog/posts/compressing-rap-vocals-essential-techniques-for-dynamic-control)
- [Rap Vocal Compression Settings — Music Guy Mixing](https://www.musicguymixing.com/rap-vocal-compression-settings/)
- [Serial Compression Guide — Music Guy Mixing](https://www.musicguymixing.com/serial-compression/)
- [What Is Audio Saturation — iZotope](https://www.izotope.com/en/learn/what-is-audio-saturation)
- [Tape Saturation Guide 2026 — Tonalyst](https://tonalyst.com/tape-saturation-emulation-guide)
- [AI Vocal Enhancer Problems — VERTU](https://vertu.com/ai-tools/why-your-ai-audio-enhancer-produces-unnatural-timbres-and-how-to-fix-it/)
- [Common AI Vocal Mistakes — Kits.AI](https://www.kits.ai/blog/ai-vocal-tips-tricks)
- [De-Essing 101 — Mike's Mix Master](https://www.mikesmixmaster.com/de-essing-101-how-to-remove-harsh-sibilance-from-vocals)
- [Spotify Pedalboard — GitHub](https://github.com/spotify/pedalboard)
- [Pedalboard API Reference](https://spotify.github.io/pedalboard/reference/pedalboard.html)
