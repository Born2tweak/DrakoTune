# Underground Vocal Engineering Reference

> Why professionally mixed underground rap vocals sound expensive, aggressive, AND listenable.
> Written for DrakoTune's DSP team. Engineering insights, not theory.
> Updated: 2026-05-20

---

## 1. The Core Paradox

Underground rap vocals must be **aggressive** and **smooth** simultaneously. This sounds contradictory but isn't — the solution is frequency-specific control:

- **Aggression** lives in the 1-3kHz fundamental energy and transient attack (first 10-20ms of each consonant)
- **Pain** lives in resonant peaks at 3.5-6kHz and uncontrolled sibilance at 5-8kHz
- **Smoothness** means the SUSTAINED portion of the vocal doesn't fatigue the ear

A professional mix preserves the initial hit of each word (punch, aggression, life) while taming the sustained resonances that cause listener fatigue.

---

## 2. Why Some Aggressive Vocals Hurt and Others Don't

### The "Controlled Danger" Philosophy

Professional engineers working on Playboi Carti, Ken Carson, Yeat, Destroy Lonely, and similar artists achieve "controlled danger" through this principle:

> **Let the transient through. Kill the resonance.**

| Element | Hurts ears | Sounds expensive |
|---------|-----------|-----------------|
| **Transients** (first 5-20ms) | Unchecked peaks clip the DAC | Fast attack doesn't squash them, but limiter catches extreme peaks |
| **Sustain** (body of each word) | Resonant peaks ring at fixed frequencies | Problem frequencies are surgically cut, sustain is warm and dense |
| **Sibilance** (S, T, F) | Full bandwidth spike, piercing | De-essed dynamically — only during sibilant moments, not always |
| **Dynamics** | Random volume jumps shock the ear | Compressed enough to feel consistent but not flat |
| **Distortion** | Digital clipping = harsh square waves | Analog-style saturation = warm odd/even harmonics |

### What Creates Ear Fatigue

Ear fatigue is NOT caused by loudness. It's caused by:

1. **Sustained energy at resonant peaks** — a constant 4kHz ring is fatiguing at any volume
2. **Crest factor too low** — over-compressed vocals tire the ear because there's no rest
3. **Uncontrolled sibilance** — piercing "S" sounds trigger a physical flinch response
4. **Intermodulation distortion** — clipped harmonics that aren't musically related to the fundamental

Professional underground vocals are LOUD but not FATIGUING because the sustained resonances are controlled while the transient energy (punch) provides micro-rests for the ear.

---

## 3. Frequency Anatomy of "Expensive" Underground Vocals

### The Five Zones

```
20-80Hz     [REMOVE]     Rumble. No useful vocal content.
80-250Hz    [WARMTH]     Body, chest. Keep controlled. Cut only if boomy.
250-500Hz   [MUD ZONE]   #1 "cheap" indicator. Almost always needs -2 to -4dB.
500Hz-2kHz  [BODY]       Core vocal intelligibility. NEVER cut broadly here.
2-4kHz      [PRESENCE]   Forward placement, clarity. Cut resonant PEAKS only.
3.5-6kHz    [DANGER]     Harshness lives here. Cut surgical, preserve average.
5-8kHz      [SIBILANCE]  Dynamic control only. Static cuts rob brightness.
8-12kHz     [DETAIL]     Consonant clarity, "expensive" quality. Gentle boost.
12-16kHz    [AIR]        "Floating" quality. Shelf boost +1-2dB max.
```

### The Three Regions That Separate Cheap from Premium

**Region 1: 250-400Hz (Mud)**
- Cheap: heavy, boomy, "recorded in a closet"
- Premium: clean, tight, warm without bloat
- Fix: PeakFilter cut at 280-350Hz, -2 to -4dB, Q=0.7-1.0
- DrakoTune: The diagnosis engine detects this. The adaptive chain handles it.

**Region 2: 3.5-5.5kHz (Harsh Resonance)**
- Cheap: constant ring, ice-pick quality, ear fatigue in 15 seconds
- Premium: forward and clear, present without stabbing
- Fix: Find the EXACT resonant peak (varies per voice, per mic, per room). Cut ONLY that peak, -3 to -5dB, narrow Q=1.5-2.5.
- DrakoTune: `_find_peak_frequency()` must be accurate. A 500Hz error here = wrong cut.

**Region 3: 10-14kHz (Air)**
- Cheap: dead, closed, muffled
- Premium: open, spacious, "floating above the beat"
- Fix: HighShelfFilter at 10kHz, +1.5 to +2.5dB. But NEVER boost if noise floor is audible.
- DrakoTune: Cross-reference rule — dullness boost blocked if noise_floor >= MODERATE.

---

## 4. Why Raw Vocals Sound Disconnected From Beats

### The "Different World" Problem

When a raw vocal sounds like it was recorded in a different room than the beat was made in, the causes are:

1. **Spectral mismatch** — the vocal's frequency balance doesn't match the beat's tonal center. If the beat is dark (low spectral centroid) and the vocal is bright (harsh peaks), they fight each other.

2. **Dynamic mismatch** — the beat is compressed and consistent; the vocal is wild and uncontrolled. The vocal jumps out on loud words and disappears on quiet ones.

3. **Spatial mismatch** — the beat has depth (reverb, delay, stereo width); the vocal is bone-dry mono with no spatial context. It sounds "pasted on top" rather than "living inside."

4. **Transient mismatch** — the beat's drums have controlled, shaped transients; the vocal's consonants are random and uncontrolled.

5. **Noise floor contrast** — the beat is digitally clean; the vocal has room noise. During quiet moments, the noise floor of the vocal is suddenly exposed.

### The "Floating Over the Beat" Effect

This is NOT achieved by making the vocal louder. It's achieved by:

1. **Clearing mud** — removing 250-400Hz buildup so the vocal doesn't compete with the beat's low-mids (808, bass, kick body)
2. **Presence placement** — a gentle 3-4kHz shelf or boost places the vocal ABOVE the beat's spectral energy (most beats have less energy in this range)
3. **Air** — 10kHz+ shelf gives the vocal a "floating" quality above the beat's ceiling
4. **Consistent dynamics** — compression makes every word equally audible, so the vocal never drops below the beat
5. **Controlled sibilance** — de-essed consonants don't "poke through" the beat unnaturally

The professional formula: **mud cut + presence clarity + air + consistent dynamics = floats over beat**

---

## 5. Saturation vs Digital Crunch

### Why This Matters for Underground Vocals

Underground producers WANT distortion on vocals. But there's a critical difference:

| Saturation (good) | Digital Crunch (bad) |
|---|---|
| Soft clipping — peaks are rounded | Hard clipping — peaks are flat-topped |
| Adds musical harmonics (2nd, 3rd) | Adds non-musical intermodulation products |
| Compresses gently as side effect | Compresses harshly with artifacts |
| Sounds "warm," "thick," "analog" | Sounds "crunchy," "broken," "cheap" |
| Created intentionally with tube/tape emulators | Created accidentally by clipping the ADC or DAW bus |
| Controlled by drive amount | Random — depends on input level |

### How to Tell the Difference in Analysis

- **Saturation**: Crest factor is moderately reduced (10-14dB). Waveform peaks are gently rounded. Harmonic series is ordered (H2, H3, H4 descending).
- **Digital clipping**: Crest factor is very low (<8dB). Waveform has flat tops at exactly +/-1.0. Harmonic series is disordered and extends to Nyquist.

### DrakoTune Implication

When the clipping detector fires:
- Mild clipping: could be intentional saturation. Process gently. Don't destroy.
- Severe clipping (>2% of samples at FS): likely accidental. Warn user. Pull gain back.
- Flat-top detection: definitely accidental. Recommend re-recording.

The system should NOT try to "fix" intentional distortion. If an artist recorded through a distortion chain on purpose, cleaning it up is the wrong move.

---

## 6. Compression Philosophy for Underground Rap

### The "Consistent But Alive" Target

| Metric | Raw (unprocessed) | Over-compressed | Sweet spot |
|--------|-------------------|-----------------|------------|
| RMS CV (dynamics) | 0.8-1.2 | 0.2-0.4 | 0.4-0.65 |
| Crest factor | 14-22dB | 6-10dB | 10-14dB |
| Gain reduction (avg) | 0 | 8-15dB | 3-5dB |
| Transient preservation | Full (chaotic) | None (flat) | Consonants hit, body controlled |

### Attack Time Is Everything

The attack time of the compressor is the single most important parameter for underground vocals:

- **Too fast (<5ms)**: Kills consonant impact. "P," "B," "K," "T" sounds lose their punch. The vocal becomes mushy and undefined. Aggressive delivery sounds weak.
- **Sweet spot (10-20ms)**: Consonants pass through uncompressed (the first 10-20ms), then the compressor engages on the sustained body. This preserves "punch" while smoothing dynamics.
- **Too slow (>30ms)**: Lets too much transient through. The compressor barely engages before the next word starts. Minimal dynamic control.

### Underground-Specific: Preserve the Performance

Rap delivery has INTENTIONAL dynamics:
- Emphasized words are louder (for impact)
- Flow has volume peaks and valleys (for rhythm)
- Whisper-to-shout transitions (for emotion)

Over-compressing kills all of these. The compressor should make the OVERALL level consistent without flattening the micro-dynamics within each phrase.

**Rule**: If the compressed vocal sounds "the same" on every word, it's over-compressed. You should still HEAR the performance's dynamics — they should just be narrower in range.

---

## 7. De-Essing Without Creating a Lisp

### Why Underground Vocals Are Especially Sibilant

1. Aggressive delivery = more air pushed through teeth = louder sibilance
2. Close mic technique = proximity effect + sibilance boost
3. Cheap condenser mics with presence peaks at 5-8kHz
4. Compression RAISES sibilance (it pushes quiet sibilants up toward loud ones)

### The Professional Approach

Professional engineers de-ess AFTER compression, not before. This is because:
- Compression raises the level of sibilant sounds relative to the body
- If you de-ess before compression, the compressor undoes your work
- De-essing after compression catches the amplified sibilance

### Static Cut vs Dynamic De-Essing

| Approach | Pros | Cons | When to use |
|----------|------|------|-------------|
| Static PeakFilter cut at 6-7kHz | Simple, no artifacts | Removes brightness from ALL moments, not just sibilant ones | Mild sibilance, Alpha-level processing |
| Dynamic EQ (sidechain) | Only cuts during sibilant moments, preserves brightness | Complex, needs detection logic | Moderate-severe sibilance, future milestone |
| VST3 de-esser plugin | Professional quality, frequency-following | External dependency | If user has FabFilter Pro-DS or similar |

### DrakoTune Alpha 2 Approach

For now: static PeakFilter cut at detected sibilant frequency, narrow Q (3.5-5.0), -2 to -5dB based on severity. Accept that this slightly dulls non-sibilant moments. Future milestone: implement frame-level dynamic de-essing.

**Critical**: Never cut more than 5dB at the sibilant frequency. Over-de-essing creates a lisp that is MORE distracting than the original sibilance.

---

## 8. The "Floating" Effect — Engineering Depth

### What Professional Underground Mixes Have That Raw Vocals Don't

The "floating over the beat" sensation comes from three simultaneous effects:

**1. Frequency Separation**
The vocal occupies a frequency "lane" that doesn't compete with the beat:
- Beat lives in: sub-bass (20-80Hz), bass body (80-200Hz), snare crack (200-400Hz + 5kHz)
- Vocal should live in: body (200-1kHz), presence (2-4kHz), air (10kHz+)
- Overlap zone (200-400Hz) is where mud lives — cutting this on the vocal lets it "separate" from the beat

**2. Dynamic Consistency**
A compressed vocal sits at a consistent level relative to the beat. Raw vocals jump above and below the beat's level unpredictably.

**3. Spatial Context**
Even a tiny amount of early reflections (5-20ms delay, very subtle) tells the brain "this voice exists in the same space as these instruments." Bone-dry vocals sound "disconnected" because they have zero spatial cues.

### How DrakoTune Achieves This (Within Alpha 2 Scope)

Steps 1 and 2 are within current scope:
1. **Mud cut** → frequency separation ✓
2. **Compression** → dynamic consistency ✓
3. **Spatial processing** → future milestone (Blend stage)

The adaptive chain's mud cut + compression already moves toward "floating." Full spatial processing comes later.

---

## 9. What Makes Vocals Sound "Cheap" — The Full Checklist

### Instant "Cheap" Indicators (fix these first)

| Rank | Indicator | What it sounds like | Fix |
|------|-----------|-------------------|-----|
| 1 | Mud buildup | "Closet recording," words blur together | PeakFilter cut 250-350Hz, -3dB |
| 2 | Harsh resonance | Ear fatigue in 15 seconds | PeakFilter cut at detected peak, -3 to -5dB |
| 3 | Uncontrolled dynamics | Some words blast, others disappear | Compression 3:1-4:1, 15ms attack |
| 4 | Background noise | Hiss/hum between phrases | Noise gate, gentle |
| 5 | Clipping artifacts | Crunchy, broken transients | Gain staging, limiter |

### Subtle "Cheap" Indicators (fix after the above)

| Rank | Indicator | What it sounds like | Fix |
|------|-----------|-------------------|-----|
| 6 | No air | Muffled, closed, dead | HighShelf boost at 10kHz, +1.5dB |
| 7 | Sibilance | "S" sounds pierce through | PeakFilter cut 5-7kHz, narrow Q |
| 8 | Boxiness | Cardboard, hollow quality | PeakFilter cut 400-700Hz, narrow surgical |
| 9 | Disconnected from beat | Pasted on top, different world | Mud cut + compression (enables blending) |
| 10 | Flat dynamics | Over-compressed, robotic | Reduce compression ratio, slower attack |

### The "Expensive" Vocal Has All of These

- Clean low-end (no mud)
- Smooth upper-mids (no harsh peaks)
- Present without fatiguing (surgical EQ, not broad cuts)
- Consistent level (compressed but dynamic)
- Air and shimmer (high shelf, subtle)
- Warmth (subtle saturation or low shelf, future milestone)
- Blends with beat (frequency separation + dynamics matching)
- Transient clarity (attack time preserves consonants)

---

## 10. Genre-Specific Notes

### Rage / Ken Carson / Destroy Lonely Style

- MORE aggression in 1-3kHz is acceptable and desired
- Distortion is often intentional — don't clean it
- Vocal sits FORWARD (louder relative to beat than in melodic rap)
- Less reverb, more dry, more "in your face"
- Compression can be heavier (4:1-6:1) because the style rewards consistency
- Sibilance is less of an issue (delivery style is less "S"-heavy)
- Air boost can be more aggressive (+2-3dB) since these vocals are meant to be bright

### Dark Trap / Atmospheric

- LESS presence boost — vocal should feel "recessed" and moody
- More reverb/delay (future milestone) for depth
- Mud cut is still essential but warmth preservation is critical
- Lower compression ratio (2.5:1-3:1) — dynamics are part of the mood
- Darker overall tone — skip or reduce air boost
- Noise floor can be slightly higher (room tone adds atmosphere)

### Distorted Melodic / Yeat / Playboi Carti Style

- Intentional vocal processing artifacts are the aesthetic
- Pitch effects, heavy saturation, auto-tune are features not bugs
- DrakoTune should detect "already heavily processed" and process minimally
- If overcompressed + saturated = intentional. Warn but don't "fix"
- The "cheap" indicators don't apply — these artists deliberately sound lo-fi
- Focus on: removing MUD only. Leave everything else.

### Headlock-Specific Analysis

Based on the listening QA feedback ("piercing, hurts ears, crunchy highs, muddy, boxy, aggressive-good, punchy-good, alive-good"):

This vocal likely has:
- **Strong fundamental delivery** (the "aggressive/punchy/alive" quality) — PRESERVE
- **Room resonance at 400-600Hz** (the "boxy" quality) — SURGICAL CUT
- **Cheap mic presence peak at 3.5-5kHz** (the "piercing/hurts" quality) — CUT AT EXACT PEAK
- **Low-mid buildup at 250-350Hz** (the "muddy" quality) — STANDARD MUD CUT
- **Possible clipping or digital edge at 8-10kHz** (the "crunchy highs") — CHECK CLIPPING, THEN GENTLE HIGH SHELF CUT

Recommended adaptive chain response:
```
HPF(80Hz) → mud cut(300Hz, -3dB) → boxy cut(500Hz, -2dB, Q=3.0) 
→ harsh peak cut(~4kHz, -4dB, Q=1.5) → sibilance cut(~7kHz, -2dB, Q=4.0)
→ gate → comp(3.5:1, 15ms attack) → limiter(-1dB)
```

What to PROTECT:
- 1-2.5kHz energy (this is where the "aggressive" lives)
- Transient attack on consonants (compressor attack must be ≥10ms)
- Dynamic variation within phrases (don't over-compress)
- Low-end warmth below 200Hz (don't over-cut with HPF)

---

## 11. Common Engineering Mistakes to Avoid

### Mistake 1: Broad EQ Instead of Surgical

**Wrong**: Cut -4dB across all of 2-8kHz with Q=0.5
**Right**: Find the ONE resonant peak at 4.2kHz and cut -4dB with Q=1.5-2.0

Broad cuts remove the good energy (presence, clarity) along with the bad (resonance). Surgical cuts remove only the ringing frequency.

### Mistake 2: Fixing Harshness with Compression

**Wrong**: "The vocal is harsh, so I'll compress it harder to bring those peaks down"
**Right**: EQ the harshness out FIRST, then compress the now-clean signal

Compressing a harsh signal makes the compressor pump on harsh frequencies, creating an inconsistent result where harsh moments are ducked but the release then sounds weird.

### Mistake 3: Boosting Presence on a Muddy Vocal

**Wrong**: "Vocal lacks clarity, boost 3kHz"
**Right**: Cut the mud at 300Hz first. The clarity was always there — it was being masked.

Boosting presence on a muddy vocal = BOTH harsh AND muddy. The mud masks the fundamental, so you boost presence to compensate, but the mud is still there causing boominess underneath.

### Mistake 4: Using the Same EQ Frequencies for Every Voice

**Wrong**: "Always cut 3.5kHz for harshness"
**Right**: Find where THIS voice resonates. It could be 3.2kHz, 4.5kHz, or 5.8kHz.

Every voice, mic, and room combination creates a unique resonant profile. The diagnosis engine MUST find the actual peak, not assume a fixed frequency.

### Mistake 5: Treating All Distortion as Bad

**Wrong**: "Clipping detected → apply -6dB gain"
**Right**: Check if distortion is intentional (artistic) or accidental (recording error)

If the artist recorded through a guitar amp or tape machine or CLA plugin, that distortion is the sound. Don't "fix" it.

### Mistake 6: Over-Gating Breaths

**Wrong**: Noise gate removes all sound between words (including breaths)
**Right**: Gate threshold just above room noise, never above breath level

Breaths are humanity. They're rhythmic. They tell the listener "a real person is here." Removing them makes vocals sound robotic. Professional mixes KEEP breaths — they just reduce the room noise around them.

---

## 12. The DrakoTune Processing Philosophy

### For Headlock and Similar Raw Underground Vocals

```
GOAL: Controlled danger. Not sterile. Not painful.
      The vocal should feel like a weapon aimed precisely,
      not like a broken speaker.

APPROACH:
  1. Diagnose what's actually wrong (don't assume)
  2. Fix the TOP 3 problems only (don't chase perfection)
  3. Preserve the energy, attack, and emotion
  4. Remove only what causes physical discomfort
  5. Leave the character intact

NEVER:
  - Cut more than -5dB at any single frequency
  - Compress more than 6dB gain reduction
  - Remove breaths
  - Flatten dynamics below CV=0.4
  - Boost highs on a noisy recording
  - Apply the same settings to a different vocal without re-diagnosing

ALWAYS:
  - Find the EXACT resonant peak before cutting
  - Preserve 1-2.5kHz fundamental energy
  - Keep compressor attack ≥10ms for transient clarity
  - Cross-reference warnings before applying contradictory actions
  - Assume the artist's delivery choices are intentional
```

### The One-Sentence Philosophy

> Remove what hurts the ear. Keep what hits the heart.

---

## 13. Practical Parameter Ranges for Underground Vocals

### EQ Cuts (Subtractive)

| Target | Frequency | Gain | Q | When |
|--------|-----------|------|---|------|
| Mud | 250-350Hz | -2 to -4dB | 0.7-1.0 | Almost always |
| Boxiness | 400-700Hz | -2 to -3dB | 2.5-4.0 | If hollow/cardboard sound |
| Harshness | 3-6kHz (find peak) | -2 to -5dB | 1.2-2.5 | If fatiguing |
| Sibilance | 5-8kHz (find peak) | -2 to -4dB | 3.5-5.0 | If S/T sounds pierce |
| Digital edge | 8-10kHz | -1 to -2dB | 1.0 | If "crunchy" quality |

### EQ Boosts (Additive) — Use Sparingly

| Target | Frequency | Gain | Q | When |
|--------|-----------|------|---|------|
| Warmth | 100-200Hz shelf | +1 to +2dB | 0.7 | If thin/cold |
| Presence | 3-4kHz | +1 to +2dB | 1.0-1.5 | If buried/recessed (AND no harshness) |
| Air | 10kHz+ shelf | +1 to +2.5dB | 0.7 | If dull/closed (AND low noise floor) |

### Compression

| Style | Threshold | Ratio | Attack | Release |
|-------|-----------|-------|--------|---------|
| Gentle (preserve dynamics) | -20dB | 2.5:1 | 20ms | 80ms |
| Standard underground | -18dB | 3.5:1 | 15ms | 60ms |
| Aggressive (rage/energy) | -16dB | 4:1 | 10ms | 50ms |
| Peak taming only | -12dB | 6:1 | 5ms | 40ms |

### Noise Gate

| Context | Threshold | Ratio | Release |
|---------|-----------|-------|---------|
| Clean recording | Skip gate entirely | — | — |
| Mild noise | noise_floor + 8dB | 1.5:1 | 200ms |
| Moderate noise | noise_floor + 10dB | 2:1 | 250ms |
| NEVER above | -30dBFS | any | — |

---

## 14. Key Takeaways for DrakoTune Implementation

1. **Diagnosis accuracy is everything.** A 500Hz error in peak detection = wrong EQ cut = worse output.

2. **Subtractive before additive.** Always cut problems before boosting qualities. Cutting mud often reveals presence naturally.

3. **The first 10ms of each word is sacred.** Compressor attack must let consonants through. This is where "punch" and "aggression" live.

4. **Cross-reference prevents disasters.** Never boost air on noisy recordings. Never boost presence on harsh vocals. Never cut mud on thin vocals.

5. **Underground vocals SHOULD sound aggressive.** The target is not "smooth jazz vocal." It's "controlled weapon." Energy and edge are features, not bugs.

6. **Less is more.** Three well-chosen EQ cuts will sound better than seven mediocre ones. Each additional plugin adds phase shift and potential artifacts.

7. **The adaptive chain should typically have 4-6 plugins, not 12.** If everything fires, something is wrong with the thresholds.

8. **Breaths, delivery emphasis, and vocal cracks are humanity.** Never process them out. They're why people connect with underground artists over polished pop.
