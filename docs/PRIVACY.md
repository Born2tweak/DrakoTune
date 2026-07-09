# DrakoTune Privacy Policy — Pilot Draft

> Draft for the controlled pilot only. Not a final or legally reviewed policy.
> Do not present DrakoTune as offering guaranteed privacy on this basis.

## What we collect

- The audio file you upload, for the purpose of analyzing and processing it.
- Optional feedback you submit (helpful yes/no and a free-text comment). Audio is
  never attached to feedback.
- We do not ask for personal information (no name, email, or account required in
  the pilot).

## How your audio is handled

- Audio is treated as private creative material.
- Processing runs on our own server. **Your audio is not sent to any third-party
  service.**
- Playback links are HMAC-signed and time-limited; there are no public audio URLs.
- Working files (original and processed) are stored privately and are deleted on
  request (`DELETE /api/jobs/{id}`) and automatically after a short retention
  window; the working area is cleared on server restart.

## What we do not do

- We do not sell or share your audio.
- We do not use your audio to train models in the pilot.
- We do not log raw audio or embed secrets/PII in reports.

## Your controls

- Delete a job (and its audio) at any time.
- Decline to submit feedback.

## Contact & scope

This is an early pilot. Data handling may change before any public release, at
which point this draft will be replaced by a reviewed policy.
