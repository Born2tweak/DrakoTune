# DrakoTune Artist Recording — Consent Protocol & Collection Kit (M29)

> Status: **DRAFT — requires human/legal approval before any recording session.**
> Policy basis: `docs/data/DATASET_GOVERNANCE.md` §6 (Tier P). No agent may
> collect, upload, or process artist audio under this protocol until a human
> marks it APPROVED here and stores the signed forms in `data/licenses/artist/`.

## 1. Purpose

Close the public-data gap (research report §16/§31): no public dataset covers
rap, melodic rap, trap, R&B, hyperpop, or bedroom-condition vocals. Collect a
small controlled corpus (5–10 consenting artists) to (a) evaluate DrakoTune on
its actual target material and (b) close the same-performance multi-microphone
gap.

## 2. Session design (per artist)

- **Takes:** 3–6 short takes (30–90 s each): at least one rap/spoken-flow, one
  sung/melodic, one ad-lib/energy take; artist's own material or cleared demo
  lyrics only.
- **Microphones:** ≥2 recorded **simultaneously**: one budget device (USB mic
  or phone) + one condenser/interface, both dry (no plugins printed).
- **Rooms:** artist's normal recording space (untreated preferred) noted as
  {untreated / partially treated / booth}.
- **Exports:** dry WAV per mic (44.1 kHz or higher, 24-bit preferred), plus
  optional: the artist's own processed version, instrumental, and reference
  tracks they aim for (references are Tier D — never stored, titles only).
- **Metadata form (per take):** genre, style, register (self-described), mic
  models, interface, room type, distance to mic, input gain notes, prior
  processing (must be none for dry takes), known issues, artist intent notes.

## 3. Consent form — required clauses (signed before recording)

1. **Ownership:** the artist owns their recordings and compositions.
2. **License to DrakoTune:** non-exclusive license to store and use the
   recordings for audio-processing evaluation, internal benchmarking, and
   product development. **Commercial use of results** (not of the recordings
   themselves) permitted.
3. **Separate opt-in checkbox (default OFF):** use in future machine-learning
   training. Without this box, the audio never enters any training set.
4. **Prohibited uses (unconditional):** no voice cloning, no voice-identity
   modeling or biometric identification, no impersonation, no synthesis of new
   performances in the artist's voice, no redistribution or publication of the
   audio.
5. **Withdrawal:** the artist may withdraw at any time by email; audio and all
   derived clips are deleted within 30 days; aggregate metrics already
   published remain (stated explicitly).
6. **Processed outputs:** any DrakoTune-processed version belongs to the
   artist and may be used by them freely.
7. **Retention:** raw audio retained at most 3 years, then deleted or
   re-consented.
8. **Age:** contributors must be 18+ (or provide guardian consent — prefer
   excluding minors entirely in v1).
9. **Privacy:** name/contact stored separately from audio; audio filed under a
   pseudonymous artist ID; no audio or PII in git (Tier P storage rules).

## 4. Storage & handling

- Audio: `data/restricted/artist/<artist_id>/take_<n>_<mic>.wav` (gitignored).
- Signed forms + metadata: `data/licenses/artist/<artist_id>/` (forms are
  scanned PDFs — **not** committed; the directory is gitignored except a
  committed `INDEX.md` listing artist IDs, consent date, and opt-in status).
- A Tier P manifest per artist in `data/manifests/` (metadata only, no names).

## 5. Evaluation reuse

The M23 benchmark and M24 listening pipeline run unchanged on this corpus
(no clean references → no-reference metrics + human A/B only). Results feed
the genre-scoped claims table in the validation plan.

## 6. Approval record

| Step | Who | Date | Status |
|---|---|---|---|
| Legal review of consent form | human | — | ☐ pending |
| Protocol approval | project owner | — | ☐ pending |
| First session authorized | project owner | — | ☐ pending |
