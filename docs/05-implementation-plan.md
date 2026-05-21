# DrakoTune — Implementation Plan v1

## Core Development Philosophy

DrakoTune **MUST** be built:

- Incrementally
- Milestone-by-milestone
- Phase-by-phase

Agents **MUST**:

- Complete one milestone fully
- Validate functionality
- Only then move to the next milestone

The repo should **NEVER** become:

- Half-built
- Over-scaffolded
- Dependent on unfinished systems

### Core Milestone Rule

> "One milestone at a time until complete."

If a milestone fails, breaks, produces unstable output, or does not meet acceptance criteria, agents **MUST** remain on that milestone until it is solved.

**DO NOT:**

- Skip ahead
- Stack unfinished systems
- Build speculative future architecture

---

## Development Order

The build order is intentionally constrained.

**Priority:**

1. Reliable audio pipeline
2. Stable processing
3. Artist UX
4. Conversational refinement
5. Aesthetic intelligence

**NOT:**

1. Advanced AI
2. Fancy infrastructure
3. Complex automation
4. Premature scaling

---

## MILESTONE ALPHA — Proof-of-Concept Audio Pipeline (ACTIVE)

**Status:** IN PROGRESS
**Started:** 2026-05-20

**The question this milestone must answer:**

> "Can DrakoTune make bad raw vocals sound noticeably smoother, less harsh, and more professionally listenable?"

### Scope

1. Accept a raw vocal WAV file as input
2. Run FFmpeg preprocessing (normalize to 44100Hz, 16-bit, mono)
3. Apply a basic Spotify Pedalboard DSP chain (cleanup stage only)
4. Generate before/after preview audio files
5. Export a processed WAV

### DSP Chain

- Highpass filter (~80Hz, remove rumble)
- Parametric EQ cut on harsh upper-mids (2-8kHz)
- Gentle compression (smooth dynamics)
- Light noise gate (reduce background noise)
- Output normalization

### Deliverables

- `src/dsp/pipeline.py` — Core Pedalboard processing chain
- `src/dsp/preprocess.py` — FFmpeg preprocessing utilities
- `src/dsp/export.py` — WAV export with before/after
- `tests/test_pipeline.py` — Pipeline tests
- `scripts/run_alpha.py` — CLI entry point

### Acceptance Criteria

- [ ] Pipeline accepts WAV and produces processed WAV
- [ ] FFmpeg normalizes input to 44100Hz/16-bit/mono
- [ ] Pedalboard applies: highpass, EQ cut, compression, noise gate
- [ ] Before/after files generated in output directory
- [ ] Processed vocal is audibly smoother than input
- [ ] Completes in under 30s for 3-minute vocal
- [ ] Tests pass with pytest
- [ ] No fake DSP — only real Pedalboard operations

### NOT in Scope

Authentication, dashboards, billing, reference matching, conversational AI, advanced infrastructure, frontend, database, Redis, deployment.

---

## MASTER ROADMAP

### Phase 0. Project Foundation

**Goal:** Create stable project structure and development environment.

#### Milestone 0.1 — Initialize Project Structure

**Tasks:**

- Frontend setup
- Backend setup
- Environment config
- Git structure
- Linting/formatting
- Package management

**Acceptance Criteria:**

- Frontend runs
- Backend runs
- Repo organized
- Lint passes
- Environment variables configured

#### Milestone 0.2 — Implement Storage Pipeline

**Tasks:**

- Upload system
- Local/cloud storage
- Audio file handling
- Metadata storage

**Acceptance Criteria:**

- Upload WAV/MP3 successfully
- Retrieve files
- Validate formats
- Prevent invalid uploads

#### Milestone 0.3 — Implement Waveform Preview

**Tasks:**

- Waveform rendering
- Playback controls
- Audio visualization

**Acceptance Criteria:**

- Uploaded audio visible
- Playback functional
- Waveform responsive

---

### Phase 1. Audio Processing Foundation

> **MOST IMPORTANT PHASE**
>
> The product does NOT exist until bad vocals become noticeably more listenable.

**Goal:** Create reliable DSP pipeline.

#### Milestone 1.1 — Integrate FFmpeg Pipeline

**Tasks:**

- Transcoding
- Normalization
- Slicing
- Render handling

**Acceptance Criteria:**

- Process uploaded audio
- Export transformed WAV
- Stable audio rendering

#### Milestone 1.2 — Integrate Spotify Pedalboard

**Tasks:**

- DSP chain execution
- EQ support
- Compressor support
- Saturation support
- Reverb support

**Acceptance Criteria:**

- Audio chains execute reliably
- Parameter control works
- Renders stable

#### Milestone 1.3 — Create Cleanup Stage

**Purpose:** Reduce harshness, improve listenability.

**Tasks:**

- De-harsh EQ
- Denoise
- De-ess
- Declip

**Acceptance Criteria:**

- Harsh vocals noticeably smoother
- No broken audio artifacts
- Preview generation works

> **THIS IS A MAJOR MILESTONE.**
>
> Do NOT move on until: "crunchy vocals sound noticeably more listenable."

#### Milestone 1.4 — Create Presence Stage

**Purpose:** Fullness, smoothness, vocal density.

**Tasks:**

- Compression
- Harmonic enhancement
- Tonal shaping

**Acceptance Criteria:**

- Vocals sound fuller
- Vocals feel more present
- No over-compression artifacts

#### Milestone 1.5 — Create Blend Stage

**Purpose:** Vocal/beat cohesion.

**Tasks:**

- Ambience
- Stereo positioning
- Depth processing

**Acceptance Criteria:**

- Vocals integrate naturally into beat
- Spatial feel improved
- Atmosphere noticeable

#### Milestone 1.6 — Create Emotion Stage

**Purpose:** Underground aesthetic enhancement.

**Tasks:**

- Saturation
- Texture shaping
- Controlled distortion
- Atmosphere enhancement

**Acceptance Criteria:**

- Vocals sound more immersive
- Emotional texture preserved
- Outputs feel stylistically intentional

#### Milestone 1.7 — Create Final Polish Stage

**Tasks:**

- Loudness optimization
- Leveling
- Final balancing

**Acceptance Criteria:**

- Commercially listenable exports
- Stable loudness
- Clean rendering

---

### Phase 2. Audio Intelligence Layer

**Goal:** Add structured analysis systems.

#### Milestone 2.1 — Integrate Librosa

**Tasks:**

- Spectral analysis
- Pitch analysis
- Harshness estimation

**Acceptance Criteria:**

- Audio feature extraction works
- Outputs structured JSON analysis

#### Milestone 2.2 — Integrate Essentia

**Tasks:**

- Timbre analysis
- Loudness profiling
- Tonal analysis

**Acceptance Criteria:**

- Advanced audio metrics functional

#### Milestone 2.3 — Integrate TorchAudio

**Tasks:**

- Transforms
- Preprocessing
- ML audio pipelines

**Acceptance Criteria:**

- Audio tensor pipeline stable

#### Milestone 2.4 — Integrate Demucs

**Tasks:**

- Source separation
- Beat/vocal isolation

**Acceptance Criteria:**

- Isolate vocals reliably
- Support beat-aware workflows

#### Milestone 2.5 — Build Structured Audio Analysis Pipeline

**Tasks:**

- Combine analysis systems
- Create unified feature profiles

**Acceptance Criteria:**

- Single structured audio profile generated
- Consistent analysis outputs

---

### Phase 3. Frontend Experience

**Goal:** Create artist-native UX.

#### Milestone 3.1 — Build Upload Interface

**Acceptance Criteria:**

- Drag/drop functional
- Upload feedback visible
- Errors handled cleanly

#### Milestone 3.2 — Build Processing Stage UI

**Acceptance Criteria:**

- Stages navigable
- Previews accessible
- Rollback works

#### Milestone 3.3 — Build Aesthetic Slider System

**Examples:** Smoother, darker, wider, atmospheric.

**Acceptance Criteria:**

- Sliders affect DSP parameters
- Changes audible

#### Milestone 3.4 — Build Real-Time Preview System

**Acceptance Criteria:**

- Fast preview generation
- Stage preview works
- Minimal latency

> **THIS IS A CRITICAL MILESTONE.**

#### Milestone 3.5 — Build Export Workflow

**Acceptance Criteria:**

- Export stable WAV
- High-quality output
- Download functional

---

### Phase 4. Conversational AI Layer

**Goal:** Translate artistic language into DSP actions.

#### Milestone 4.1 — Build Prompt Interpretation Layer

**Tasks:**

- Parse emotional descriptors
- Classify intent

**Acceptance Criteria:**

- Prompts produce structured interpretations

#### Milestone 4.2 — Build Parameter Mapping System

**Tasks:**

- Map language to DSP controls

**Examples:**

- "less harsh" → EQ smoothing

**Acceptance Criteria:**

- Predictable mappings
- Bounded parameter ranges

#### Milestone 4.3 — Build Conversational Refinement Loop

**Acceptance Criteria:**

- Iterative refinement works
- Conversation updates processing
- Changes remain stable

#### Milestone 4.4 — Build Explanation System

**Example:** "Added saturation for warmth and density."

**Acceptance Criteria:**

- Understandable explanations
- Artist-friendly language

---

### Phase 5. Aesthetic Intelligence

**Goal:** Develop aesthetic-aware processing.

#### Milestone 5.1 — Build Aesthetic Profiles

**Examples:**

- Dark Atmospheric
- Underground Intimate
- Rage Aggressive
- Dreamy Ambient

**Acceptance Criteria:**

- Profiles audibly distinct
- Profiles stable

#### Milestone 5.2 — Build Reference Track Guidance

**NOT** cloning.

**Purpose:**

- Ambience matching
- Tonal guidance
- Spatial guidance

**Acceptance Criteria:**

- Reference tracks improve results meaningfully

#### Milestone 5.3 — Build Taste Memory System

**Tasks:**

- Remember user preferences
- Adapt workflows over time

**Acceptance Criteria:**

- User-specific improvements noticeable

---

### Phase 6. Stability & QA

**Goal:** Ensure production reliability.

#### Milestone 6.1 — Stress Test Audio Pipeline

**Acceptance Criteria:**

- Large uploads stable
- No crashes
- Corrupted audio handled safely

#### Milestone 6.2 — Latency Optimization

**Acceptance Criteria:**

- Previews under target latency
- Exports performant

#### Milestone 6.3 — Cross-Browser Testing

**Acceptance Criteria:**

- Stable on major browsers

#### Milestone 6.4 — Audio Quality Validation

**Acceptance Criteria:**

- Outputs consistently listenable
- No severe artifacts
- Emotional texture preserved

---

### Phase 7. Deployment

**Goal:** Deploy stable MVP.

#### Milestone 7.1 — Production Infrastructure Setup

**Tasks:**

- Vercel
- Backend hosting
- Storage
- Environment variables

**Acceptance Criteria:**

- Production deployment functional

#### Milestone 7.2 — Production Audio Pipeline Validation

**Acceptance Criteria:**

- Uploads stable in production
- Rendering stable
- Exports functional

#### Milestone 7.3 — Beta Release

**Acceptance Criteria:**

- Real users onboarded
- Feedback collection active
- Crash monitoring active

---

## GLOBAL ACCEPTANCE RULES

Before **ANY** milestone is considered complete:

### MUST PASS

- Build compiles
- Lint passes
- Feature functional
- Audio output valid
- No major console errors
- No broken UI
- Milestone tested manually

---

## GLOBAL FAILURE RULES

**DO NOT** move forward if:

- Audio sounds broken
- Outputs are robotic
- Latency unacceptable
- Previews fail
- Stages unstable
- Artifacts severe
- Functionality incomplete

---

## MOST IMPORTANT SUCCESS METRIC

The MVP succeeds when:

> "Bad vocals become emotionally and commercially listenable."

**NOT:**

> "The AI is technically impressive."
