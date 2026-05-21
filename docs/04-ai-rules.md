# DrakoTune — AI Rules v1

## Purpose

These rules govern **ALL** AI coding agents, orchestration agents, architecture agents, and implementation agents working on DrakoTune.

The purpose is to:

- Prevent spaghetti architecture
- Prevent hallucinated engineering
- Maintain product direction
- Ensure realistic audio-system implementation

---

## CORE RULES

### 1. NEVER Reinvent Proven Audio Systems

Agents **MUST** use existing proven systems whenever possible.

Required systems:

- Spotify Pedalboard
- FFmpeg
- Librosa
- Essentia
- TorchAudio
- Demucs
- Professional DSP chains
- Proven audio-processing workflows

Agents **MUST NOT**:

- Invent fake DSP algorithms
- Recreate solved audio-processing primitives
- Fabricate nonexistent audio engineering logic

---

### 2. DrakoTune Is NOT AGI Audio Engineering

Agents **MUST** understand:

DrakoTune is **AI-assisted DSP orchestration** — NOT fully autonomous magical AI mixing.

The product relies on:

- Constrained workflows
- Deterministic DSP
- Structured parameter mappings
- Human-in-the-loop refinement

---

### 3. LLMs Are NOT The Audio Engine

LLMs **ONLY**:

- Interpret artistic intent
- Map language into structured actions
- Assist refinement workflows
- Orchestrate processing systems

LLMs **MUST NOT**:

- Freestyle DSP behavior
- Generate fake engineering logic
- Directly manipulate raw audio without constrained systems

---

### 4. NEVER Build Multiple Major Systems Simultaneously

Agents **MUST**:

- Complete one implementation phase fully
- Verify functionality
- Then proceed

**DO NOT:**

- Partially implement multiple systems
- Create unfinished architecture
- Scaffold fake functionality

---

### 5. Build Incrementally

Every phase **MUST**:

- Function independently
- Be testable
- Remain stable

Each milestone should:

- Compile
- Run
- Produce usable output

---

### 6. NEVER Touch Unrelated Files

Agents **MUST**:

- Isolate changes
- Minimize scope
- Avoid unnecessary edits

**DO NOT:**

- Refactor unrelated systems
- Restructure entire repos
- Modify architecture without approval

---

### 7. ALWAYS Use Existing Patterns

Before building:

- Inspect existing codebase patterns
- Follow current conventions
- Reuse utilities
- Reuse architecture
- Reuse components

Avoid:

- Duplicated systems
- Inconsistent abstractions
- Random frameworks
- Unnecessary complexity

---

### 8. Prioritize Emotional Listenability

The product's goal is **emotionally compelling vocals** — NOT mathematically perfect audio.

Agents **MUST** avoid:

- Over-cleaning
- Sterilizing texture
- Flattening dynamics
- Removing emotional grit unnecessarily

---

### 9. Preserve Vocal Humanity

Agents **MUST** preserve:

- Texture
- Breath
- Grit
- Emotional imperfections
- Natural movement

**DO NOT:**

- Aggressively normalize everything
- Flatten transients excessively
- Produce "podcast voice" outputs

---

### 10. Underground Aesthetic Awareness

DrakoTune is optimized for:

- Underground rap
- Melodic rap
- Rage
- Atmospheric vocals
- Emotionally textured performances

Agents **MUST** understand:

- Controlled distortion may be desirable
- Saturation may be intentional
- Ambience matters heavily
- "Clean" is NOT always better

---

### 11. Conversational UX First

Users are **NOT** engineers.

Users communicate emotionally:

- "less harsh"
- "more cinematic"
- "blend better"
- "less robotic"
- "more expensive"

Agents **MUST** prioritize:

- Vibe-native UX
- Emotional descriptors
- Artist language
- Conversational refinement

Avoid:

- Engineering-heavy interfaces
- Exposing unnecessary technical complexity
- Requiring DSP expertise

---

### 12. DSP First, AI Second

Priority order:

1. Proven DSP
2. Structured analysis
3. Constrained AI orchestration
4. Conversational refinement

**NOT:**

1. Giant LLM
2. Magical black-box generation

---

### 13. Real-Time Performance Matters

Agents **MUST** optimize:

- Preview speed
- Responsiveness
- Staged rendering
- Iteration speed

Avoid:

- Unnecessary heavyweight pipelines
- Blocking operations
- Inefficient rendering loops

---

### 14. No Fake Features

Agents **MUST NOT**:

- Mock impossible capabilities
- Fabricate AI intelligence
- Create fake "coming soon" systems
- Imply functionality that does not exist

Every implemented feature **MUST**:

- Function
- Process real audio
- Be testable

---

### 15. Every Processing Stage Must Be Isolated

Stages:

1. Cleanup
2. Presence
3. Blend
4. Emotion
5. Final Polish

Each stage **MUST**:

- Be independently testable
- Support preview
- Support rollback
- Expose adjustable parameters

---

### 16. Constrained Parameter Mapping Only

User language **MUST** map into:

- Structured DSP parameters
- Bounded value ranges
- Deterministic processing actions

**DO NOT:**

- Allow unconstrained AI behavior
- Generate arbitrary plugin chains
- Create random processing paths

---

### 17. Reference Tracks Are Guidance, NOT Cloning

Reference tracks may guide:

- Tonal balance
- Ambience
- Depth
- Saturation
- Cohesion

**DO NOT:**

- Imitate artists directly
- Clone vocal identities
- Promise artist replication

---

### 18. Mobile Is NOT Priority

Primary target: **desktop web app**.

Avoid:

- Premature mobile optimization
- Unnecessary responsive complexity
- Mobile-first architecture

---

### 19. Commit Only Working Milestones

Agents **MUST**:

- Test before commit
- Lint before commit
- Verify audio outputs
- Verify exports
- Verify previews

**DO NOT:**

- Commit broken systems
- Merge speculative code
- Leave unstable architecture

---

### 20. Keep The Product Vision Intact

DrakoTune exists to help artists finally hear themselves sound professionally listenable.

Everything should support:

- Emotional realism
- Smoothness
- Atmosphere
- Texture
- Immersion
- Artist confidence

**NOT:**

- Generic AI gimmicks
- Fake autonomy
- Sterile engineering perfection

---

### 21. Living Context Rule

The project must maintain `/docs/DRAKOTUNE_CONTEXT_EXPORT.md` as a portable project brain.

**The Orchestrator MUST:**

- Read `DRAKOTUNE_CONTEXT_EXPORT.md` before starting any work session.
- Update `DRAKOTUNE_CONTEXT_EXPORT.md` before ending any work session.

**All sub-agents MUST:**

- Read `DRAKOTUNE_CONTEXT_EXPORT.md` at the start of each session to understand current state.
- Report all meaningful changes to the Orchestrator for consolidation into the context export.

**Purpose:**

This rule ensures context can move seamlessly between Claude Code, ChatGPT, Antigravity, and any future agents without requiring a full repo re-read.

See `/docs/CONTEXT_UPDATE_PROTOCOL.md` for the exact update rules and triggers.
