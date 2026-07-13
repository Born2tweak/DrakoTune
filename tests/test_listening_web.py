"""In-browser listening-session runner tests (M43)."""

import csv
import json

import numpy as np
import pytest
import soundfile as sf

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from src.webapp import app, listening  # noqa: E402

client = TestClient(app)
SR = 44100


@pytest.fixture()
def session(tmp_path, monkeypatch):
    stim = tmp_path / "stimuli"
    stim.mkdir()
    tone = (0.1 * np.sin(2 * np.pi * 220 * np.arange(SR) / SR)).astype("float32")
    trials = []
    for i in (1, 2):
        tid = f"t{i:03d}"
        for side in ("A", "B"):
            sf.write(stim / f"{tid}_{side}.wav", tone, SR, subtype="PCM_16")
        trials.append({"trial": tid, "kind": "defect", "processed_is": "B",
                       "clip_id": f"c{i}", "family": "noise", "severity": "strong"})
    (tmp_path / "session_key.json").write_text(json.dumps({"trials": trials}))
    monkeypatch.setenv("DRAKOTUNE_LISTENING_SESSION", str(tmp_path))
    return tmp_path


def test_no_session_configured(monkeypatch):
    monkeypatch.delenv("DRAKOTUNE_LISTENING_SESSION", raising=False)
    r = client.get("/listen")
    assert r.status_code == 200 and "No session configured" in r.text


def test_full_listener_flow(session):
    # start page
    r = client.get("/listen")
    assert "Start" in r.text
    # first trial page: blinded players + form
    r = client.get("/listen", params={"listener_id": "tester", "listener_type": "artist"})
    assert "trial t001" in r.text and r.text.count("<audio") == 2
    assert "session_key" not in r.text  # truth never reaches the browser
    # audio is served only with a valid signature
    bad = client.get("/listen/audio/t001/A", params={"exp": 0, "sig": "nope"})
    assert bad.status_code == 403
    # submit both trials
    for tid in ("t001", "t002"):
        r = client.post("/listen", data={"trial": tid, "listener_id": "tester",
                                         "listener_type": "artist", "preference": "B",
                                         "strength": "4", "artifacts": ["pumping"],
                                         "notes": "ok"}, follow_redirects=False)
        assert r.status_code == 303
    # done page
    r = client.get("/listen", params={"listener_id": "tester"})
    assert "Done" in r.text
    # responses CSV is analyze-compatible
    with open(session / "responses_web.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 2
    assert rows[0]["preference(A/B/none)"] == "B"
    assert rows[0]["artifact_pumping"] == "1"
    assert set(rows[0]).issuperset({"listener_id", "trial", "strength(1-5)", "notes"})


def test_invalid_submission_rejected(session):
    r = client.post("/listen", data={"trial": "t999", "listener_id": "x",
                                     "listener_type": "listener", "preference": "B",
                                     "strength": "", "notes": ""})
    assert r.status_code == 400
