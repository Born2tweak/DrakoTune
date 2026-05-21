# DrakoTune — Architecture Document v1

## Product Type

AI-assisted underground vocal engineering web app.

---

## Core Architecture Philosophy

DrakoTune is **NOT**:

- A fully autonomous AI engineer
- A custom DSP research lab
- A "magic black box" audio generator

DrakoTune **IS**:

- A constrained AI-assisted DSP orchestration platform

The system combines:

- Proven DSP frameworks
- Audio analysis systems
- Professional vocal engineering structures
- Conversational aesthetic interpretation

### Primary Architectural Principle

> "Use existing proven audio systems first. Build orchestration and aesthetic intelligence on top."

Agents **MUST**:

- Leverage existing DSP/audio frameworks
- Avoid reinventing solved audio-processing problems
- Avoid hallucinating fake engineering systems

---

## System Overview

### High-Level Stack

#### Frontend

- Next.js
- TypeScript
- TailwindCSS
- Zustand or React Context
- Wavesurfer.js for waveform preview

#### Backend

- Python FastAPI service
- Node.js orchestration layer if needed
- Redis job queue
- FFmpeg processing pipeline

#### AI / Audio Layer

- Spotify Pedalboard
- Librosa
- Essentia
- TorchAudio
- Demucs
- DSP plugin chains

#### Conversational Layer

- Claude/OpenAI API
- Structured orchestration prompts
- Constrained parameter translation

#### Infrastructure

- Vercel frontend
- Railway/Render/Fly.io backend
- Supabase/Postgres
- Cloudflare R2 or S3-compatible storage

---

## Core System Layers

### Layer 1. Frontend UX Layer

#### Purpose

Artist-facing experience.

Handles:

- Uploads
- Waveform previews
- Stage navigation
- Aesthetic controls
- Conversational interface
- Exports

#### Required UX Principles — Emotionally Intelligent UI

The app should feel:

- Futuristic
- Luxurious
- Cinematic
- Underground
- Smooth

**NOT:**

- Engineering-heavy
- Corporate
- Technical

#### Frontend Features

**Upload System**

Supports:

- Vocal WAV/MP3
- Optional beat
- Optional reference track

**Processing Stages UI**

Users can navigate:

1. Cleanup
2. Presence
3. Blend
4. Emotion
5. Final Polish

Each stage supports:

- Preview
- Rollback
- Intensity adjustments
- AI feedback

**Conversational Input**

Natural language refinement:

- "less harsh"
- "blend more"
- "more cinematic"
- "less robotic"
- "darker"
- "more emotional"

**Aesthetic Sliders**

Examples:

- Smoothness
- Ambience
- Darkness
- Width
- Aggression
- Atmosphere
- Polish

**Audio Preview**

Waveform playback:

- Before/after
- Stage comparison
- Low-latency previews

---

### Layer 2. Orchestration Backend

#### Purpose

Coordinate:

- Uploads
- Processing jobs
- Audio analysis
- DSP execution
- AI interpretation

#### Backend Stack

**FastAPI**

Primary audio backend. Handles:

- Processing requests
- DSP orchestration
- ML orchestration
- Queue management

**Redis Queue**

Used for:

- Audio jobs
- Staged rendering
- Async processing

**FFmpeg**

Handles:

- Transcoding
- Normalization
- Waveform extraction
- Audio slicing
- Rendering operations

---

### Layer 3. Audio Intelligence Layer

#### Purpose

Analyze audio characteristics.

This layer does **NOT** freestyle engineering. It extracts structured information used by DSP orchestration.

#### Core Audio Systems

**Librosa**

Used for:

- Spectral analysis
- Pitch analysis
- Harshness estimation
- Transient analysis
- Feature extraction

**Essentia**

Used for:

- Timbre analysis
- Loudness analysis
- Texture analysis
- Tonal profiling
- Aesthetic indicators

**TorchAudio**

Used for:

- Transforms
- Preprocessing
- ML inference
- Audio tensor workflows

**Demucs**

Used for:

- Source separation
- Beat/vocal isolation
- Preprocessing

---

### Layer 4. DSP Execution Layer

#### Purpose

Perform deterministic audio processing. This is the **TRUE audio engine**.

#### DSP Core

**Spotify Pedalboard**

Primary DSP framework. Handles:

- EQ
- Compression
- Clipping
- Saturation
- Delay
- Reverb
- Chain execution

**DSP Plugins**

Professional DSP chains. Examples:

- Compressors
- Saturators
- Stereo imagers
- Harmonic enhancers

**Professional Vocal Chains**

Used as:

- Architectural references
- Tuning inspiration
- Aesthetic baselines

**NOT** copied blindly.

**Custom DrakoTune Chains**

Custom aesthetic chains designed for:

- Underground rap
- Atmospheric vocals
- Rage textures
- Melodic ambience
- Emotional vocal presence

---

### Layer 5. Conversational Taste Layer

#### Purpose

Translate artistic language into structured DSP actions.

#### Important Rule

The LLM is **NOT**:

- The DSP engine
- The mastering engineer
- The audio processor

The LLM **ONLY**:

- Interprets artistic intent
- Maps language into structured parameter changes
- Orchestrates existing systems

#### Example Workflow

**User Input:** "This sounds crunchy and cheap."

↓

**LLM Interpretation:**

- Reduce upper-mid harshness
- Soften clipping
- Increase ambience
- Smooth transients
- Widen stereo slightly

↓

**Structured Parameters:**

JSON/object output:

- EQ settings
- Saturation values
- Ambience intensity
- Compressor behavior

↓

**DSP Execution:**

Pedalboard/plugins apply processing.

---

## Data Flow

```
Upload (Frontend → Storage)
    ↓
Analysis (Audio Intelligence Layer)
    ↓
Structured Feature Extraction (JSON feature profile)
    ↓
Conversational Interpretation (LLM orchestration)
    ↓
DSP Chain Selection (Structured processing pipeline)
    ↓
Audio Rendering (FFmpeg + Pedalboard)
    ↓
Preview Generation (Frontend playback)
    ↓
Export
```

---

## Database Schema (High-Level)

### Users

- id
- email
- username
- created_at

### Projects

- id
- user_id
- title
- created_at

### AudioFiles

- id
- project_id
- file_type
- storage_path
- duration
- waveform_data

### ProcessingStages

- id
- project_id
- stage_type
- parameters
- render_path

### Conversations

- id
- project_id
- prompt
- interpreted_actions
- created_at

---

## Storage Architecture

### Object Storage

Use:

- Cloudflare R2
- OR Supabase Storage
- OR S3-compatible system

Stores:

- Raw uploads
- Preview renders
- Exports
- Waveform assets

---

## Security Rules

### MUST

- Validate uploads
- Limit file sizes
- Sandbox processing jobs
- Rate-limit AI requests
- Isolate user files

### MUST NOT

- Execute arbitrary plugins unsafely
- Expose filesystem access
- Allow unrestricted shell execution
- Hallucinate unsafe processing behavior

---

## Performance Goals

### Preview Latency

Target: under 5–10 seconds for previews.

### Full Export

Target: under 1–2 minutes.

---

## Architecture Constraints

### MUST USE

- Pedalboard
- FFmpeg
- Librosa
- Essentia
- TorchAudio
- Demucs

as foundational primitives whenever applicable.

### MUST NOT

- Reinvent DSP algorithms unnecessarily
- Create fake "AI magic" systems
- Rely on uncontrolled LLM behavior
- Attempt AGI-style autonomous mixing

---

## MVP Architecture Goal

> "Reliable AI-assisted vocal enhancement through constrained orchestration of proven audio systems."
