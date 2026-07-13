"""In-browser blinded listening-session runner (M43).

Serves a prepared M24 session (scripts/listening_prepare.py output) so a
listener only needs a URL: one trial per page, blinded A/B players, the
artifact checklist, and responses appended to a per-session CSV compatible
with scripts/listening_analyze.py. The session key (truth) is never sent to
the browser. Local pilot use; audio served through the existing signed-URL
mechanism (no public paths).

Enable by setting DRAKOTUNE_LISTENING_SESSION to a session directory.
"""

import csv
import html
import json
import os
from pathlib import Path

LISTENING_VERSION = "1.0.0"

ARTIFACTS = ("pumping", "gated_breath_or_word_cut", "lisp_or_dulled_s",
             "hollow_comb_tone", "added_noise", "distortion",
             "lost_presence_or_air", "robotic_unnatural", "other")


def session_dir() -> Path | None:
    raw = os.environ.get("DRAKOTUNE_LISTENING_SESSION", "")
    path = Path(raw) if raw else None
    return path if path and (path / "session_key.json").exists() else None


def trial_ids(session: Path) -> list[str]:
    key = json.loads((session / "session_key.json").read_text(encoding="utf-8"))
    return [t["trial"] for t in key["trials"] if "skipped" not in t]


def stimulus_path(session: Path, trial: str, side: str) -> Path | None:
    if side not in ("A", "B") or not trial.replace("t", "").isdigit():
        return None
    path = session / "stimuli" / f"{trial}_{side}.wav"
    return path if path.exists() else None


def _responses_file(session: Path) -> Path:
    return session / "responses_web.csv"


def answered_trials(session: Path, listener_id: str) -> set[str]:
    path = _responses_file(session)
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf-8") as fh:
        return {row["trial"] for row in csv.DictReader(fh)
                if row.get("listener_id") == listener_id}


def record_response(session: Path, listener_id: str, listener_type: str, trial: str,
                    preference: str, strength: str, artifacts: list[str], notes: str) -> None:
    if trial not in trial_ids(session):
        raise ValueError("unknown trial")
    if preference.upper() not in ("A", "B", "NONE"):
        raise ValueError("preference must be A, B, or none")
    path = _responses_file(session)
    header = ["listener_id", "listener_type", "trial", "preference(A/B/none)",
              "strength(1-5)"] + [f"artifact_{a}" for a in ARTIFACTS] + ["notes"]
    new_file = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow(header)
        writer.writerow([listener_id[:40], listener_type[:20], trial,
                         preference.upper() if preference.upper() != "NONE" else "none",
                         strength]
                        + ["1" if a in artifacts else "" for a in ARTIFACTS]
                        + [notes[:500]])


def render_trial_page(trial: str, remaining: int, total: int, listener_id: str,
                      listener_type: str, a_src: str, b_src: str) -> str:
    checks = "".join(
        f'<label style="display:inline-block;margin:4px 10px 4px 0">'
        f'<input type="checkbox" name="artifacts" value="{a}"> {html.escape(a.replace("_", " "))}</label>'
        for a in ARTIFACTS)
    return (
        f"<h1>Listening test — trial {html.escape(trial)}</h1>"
        f'<p class="hint">{total - remaining + 1} of {total}. Fixed volume; some '
        "pairs are identical on purpose — <em>none</em> is a valid answer.</p>"
        '<div class="ab">'
        f'<figure><figcaption>A</figcaption><audio controls preload="none" src="{a_src}"></audio></figure>'
        f'<figure><figcaption>B</figcaption><audio controls preload="none" src="{b_src}"></audio></figure>'
        "</div>"
        '<form class="card" action="/listen" method="post">'
        f'<input type="hidden" name="trial" value="{html.escape(trial)}">'
        f'<input type="hidden" name="listener_id" value="{html.escape(listener_id)}">'
        f'<input type="hidden" name="listener_type" value="{html.escape(listener_type)}">'
        "<p><strong>Which sounds better overall?</strong> "
        '<label><input type="radio" name="preference" value="A" required> A</label> '
        '<label><input type="radio" name="preference" value="B"> B</label> '
        '<label><input type="radio" name="preference" value="none"> no difference</label></p>'
        '<p><label>How much better? (1 barely – 5 much) '
        '<select name="strength"><option value=""></option>'
        + "".join(f'<option value="{i}">{i}</option>' for i in range(1, 6))
        + "</select></label></p>"
        f"<p><strong>Problems heard (optional):</strong><br>{checks}</p>"
        '<p><label>Notes <input name="notes" maxlength="500" style="width:60%"></label></p>'
        '<button type="submit">Save & next</button>'
        "</form>"
    )


def render_start_page(total: int) -> str:
    return (
        "<h1>Listening test</h1>"
        f'<p class="hint">{total} short A/B trials. Use headphones at a comfortable '
        "fixed volume. You will not be told which version is processed.</p>"
        '<form class="card" action="/listen" method="get">'
        '<p><label>Your name or alias <input name="listener_id" required maxlength="40"></label></p>'
        "<p><label>You are a "
        '<select name="listener_type"><option>artist</option><option>engineer</option>'
        "<option selected>listener</option></select></label></p>"
        '<button type="submit">Start</button></form>'
    )


def render_done_page(listener_id: str) -> str:
    return (f"<h1>Done — thank you, {html.escape(listener_id)}!</h1>"
            '<p class="hint">Your responses were saved. You can close this page.</p>')
