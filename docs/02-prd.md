# DrakoTune — Product Requirements Document (PRD) v2

## Product Type

AI-assisted underground vocal engineering platform.

## Product Mission

Help artists transform harsh, low-quality recordings into emotionally immersive, studio-quality vocals using AI-assisted DSP orchestration and conversational aesthetic control.

## Primary Insight

Artists usually understand **how music SHOULD feel emotionally**, but NOT **how to technically engineer vocals**.

DrakoTune bridges this gap.

## Core Product Principle

> "Translate artistic intent into professional vocal engineering."

---

## Architectural Principle

DrakoTune **MUST** use:

- Existing proven DSP/audio systems
- Audio ML frameworks
- Professional vocal engineering concepts

Instead of attempting to invent entirely new audio processing systems from scratch.

The product's innovation layer is:

- Orchestration
- Workflow
- Aesthetic interpretation
- Artist-native interaction

**NOT:** reinventing DSP mathematics.

---

## System Architecture Philosophy

### Layer 1. DSP Core

**Deterministic processing.**

Uses:

- Spotify Pedalboard
- FFmpeg
- DSP plugin chains
- Professional vocal chain structures

Handles:

- EQ
- Compression
- Saturation
- Clipping
- Ambience
- Stereo processing
- Loudness optimization

### Layer 2. Audio Intelligence Layer

**Analysis and classification.**

Uses:

- Librosa
- Essentia
- TorchAudio
- Demucs

Handles:

- Vocal analysis
- Harshness detection
- Tonal balance
- Vocal texture
- Dynamics
- Vocal/beat cohesion
- Aesthetic indicators

### Layer 3. Conversational Taste Layer

**Natural language interpretation.**

Uses:

- LLM orchestration

Handles:

- Emotional interpretation
- Artistic intent translation
- Refinement suggestions
- Conversational guidance

The LLM layer **MUST NOT** directly invent audio engineering logic.

It must orchestrate:

- Existing DSP systems
- Constrained parameter mappings
- Structured processing workflows

---

## User Stories

### Non-Technical Artist

As an artist, I want to describe problems emotionally, so I can improve my vocals without learning engineering terminology.

### Underground Artist

As an underground artist, I want my vocals to sound immersive and expensive, without losing emotional texture or identity.

### Iterative Refinement

As a user, I want progressive stage-based refinement, so I can collaborate with the AI instead of receiving a mysterious one-click output.

### Professional Listenability

As a user, I want my vocals to sound commercially listenable, so I feel confident sharing and releasing music.

---

## Processing Stages

### Stage 1. Cleanup

**Goals:** Remove harshness, reduce painful frequencies, improve raw listenability.

**Uses:** EQ, de-essing, denoise, declipping.

### Stage 2. Presence

**Goals:** Smoothness, fullness, vocal density, clarity.

**Uses:** Compression, harmonic enhancement, leveling.

### Stage 3. Blend

**Goals:** Vocal integration with beat, atmosphere, depth.

**Uses:** Ambience, stereo positioning, reverb/delay balancing.

### Stage 4. Emotion

**Goals:** Cinematic enhancement, underground texture, emotional realism.

**Uses:** Saturation, texture shaping, controlled distortion, aesthetic DSP chains.

### Stage 5. Final Polish

**Goals:** Final loudness, presentation quality, export readiness.

---

## Conversational UX Requirements

The AI must support natural language feedback:

- "less crunchy"
- "more atmospheric"
- "more emotional"
- "less robotic"
- "blend into beat better"
- "smoother"
- "darker"
- "more expensive"

The system should map these phrases into **constrained DSP actions**, not hallucinated engineering logic.

---

## Real-Time Requirements

The system should support:

- Fast preview iteration
- Stage-by-stage refinement
- Near-real-time feedback loops

---

## Success Criteria

### Technical Success

- Vocals become smoother and more cohesive
- Harshness significantly reduced
- Vocals integrate naturally into beat
- Outputs sound commercially listenable

### Emotional Success

Users feel:

- Excitement
- Confidence
- Immersion
- Emotional connection to their music

---

## Failure Conditions

The system fails if outputs sound:

- Robotic
- Sterile
- Over-clean
- Emotionally flattened
- Disconnected from underground aesthetics

---

## MVP Definition

A web app that:

- Accepts raw vocals
- Analyzes aesthetic/audio qualities
- Progressively enhances vocals
- Allows conversational refinement
- Orchestrates proven DSP/audio systems
- Outputs emotionally immersive studio-quality vocals for underground artists
