"""Workstation surface tests (DT-97).

Covers the server side of the browser route: the static app is served, the mode
discovery contract is stable, an upload with a mode + macros completes, and the
A/B pair the client plays is the loudness-matched one.

Transport behaviour itself (sample-locked dual sources, gain crossfade, seeking)
is browser-side and was verified by driving the real page; what is pinned here is
everything the client depends on the server to provide.
"""

import json

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from src.modes import build_graph
from src.modes.macros import CENTRE, MACRO_NAMES, apply_macros, parse_macros
from src.webapp.app import app

FIXTURE = "fixtures/audio/muddy.wav"


@pytest.fixture
def client():
    return TestClient(app)


class TestStaticSurface:
    def test_root_serves_the_workstation_not_the_report_page(self, client):
        body = client.get("/").text
        assert 'id="app"' in body and "/static/app.js" in body

    def test_legacy_report_page_still_reachable(self, client):
        """Routing moved; the old surface was not deleted."""
        assert client.get("/classic").status_code == 200

    def test_client_assets_are_served(self, client):
        for path in ("/static/app.js", "/static/styles.css"):
            assert client.get(path).status_code == 200

    def test_page_leads_with_capability_not_apology(self, client):
        body = client.get("/").lower() if isinstance(client.get("/"), str) else client.get("/").text.lower()
        for phrase in ("not a professional mix", "unvalidated",
                       "ai makes it better", "not a professional"):
            assert phrase not in body

    def test_retention_notice_is_still_present(self, client):
        """Disclaimers were removed; operationally necessary facts were not."""
        body = client.get("/").text.lower()
        assert "deleted automatically" in body and "experimental" in body


class TestModeDiscovery:
    def test_contract_shape(self, client):
        body = client.get("/api/modes").json()
        assert body["default_mode"] in [m["name"] for m in body["modes"]]
        for m in body["modes"]:
            assert {"name", "title", "summary", "capabilities",
                    "default_intensity"} <= set(m)
            assert m["capabilities"], f"{m['name']} advertises nothing"

    def test_every_default_intensity_is_valid(self, client):
        body = client.get("/api/modes").json()
        for m in body["modes"]:
            assert m["default_intensity"] in body["intensities"]


class TestUploadRoute:
    def test_upload_with_mode_and_macros(self, client):
        with open(FIXTURE, "rb") as fh:
            resp = client.post(
                "/api/audio/upload",
                files={"file": ("v.wav", fh, "audio/wav")},
                data={"mode": "rescue", "intensity": "bold",
                      "macros": json.dumps({"body": 90, "space": 85})},
            )
        body = resp.json()
        assert body["status"] == "completed"
        assert body["macros"]["changed"], "macros were accepted but changed nothing"

    def test_response_carries_the_matched_ab_pair(self, client):
        with open(FIXTURE, "rb") as fh:
            body = client.post("/api/audio/upload",
                               files={"file": ("v.wav", fh, "audio/wav")},
                               data={"mode": "modern_rap"}).json()
        urls = body["audio_urls"]
        assert "before_preview" in urls and "after_preview" in urls
        assert body["previews_matched"] is True

    def test_playback_urls_are_signed(self, client):
        with open(FIXTURE, "rb") as fh:
            body = client.post("/api/audio/upload",
                               files={"file": ("v.wav", fh, "audio/wav")}).json()
        for url in body["audio_urls"].values():
            assert "sig=" in url and "exp=" in url

    def test_unsigned_audio_access_is_refused(self, client):
        with open(FIXTURE, "rb") as fh:
            body = client.post("/api/audio/upload",
                               files={"file": ("v.wav", fh, "audio/wav")}).json()
        assert client.get(f"/api/audio/{body['job_id']}/after").status_code == 403

    def test_signed_audio_is_decodable(self, client, tmp_path):
        with open(FIXTURE, "rb") as fh:
            body = client.post("/api/audio/upload",
                               files={"file": ("v.wav", fh, "audio/wav")},
                               data={"mode": "rescue"}).json()
        resp = client.get(body["audio_urls"]["after_preview"])
        assert resp.status_code == 200
        out = tmp_path / "a.wav"
        out.write_bytes(resp.content)
        audio, _ = sf.read(str(out), dtype="float32")
        assert audio.size > 0 and np.all(np.isfinite(audio))


class TestMacros:
    def test_centre_is_a_no_op(self):
        graph = build_graph("rescue", "bold")
        adjusted, report = apply_macros(graph, {n: CENTRE for n in MACRO_NAMES})
        assert adjusted.describe() == graph.describe()
        assert not report.changed

    def test_macros_change_the_graph(self):
        graph = build_graph("rescue", "bold")
        adjusted, report = apply_macros(graph, {"body": 100, "space": 100})
        assert adjusted.describe() != graph.describe()
        assert report.changed

    def test_source_graph_is_not_mutated(self):
        """A revision must stay reproducible from mode + macro values."""
        graph = build_graph("rescue", "bold")
        original = graph.describe()
        apply_macros(graph, {"body": 100, "space": 0})
        assert graph.describe() == original

    def test_inert_macros_are_reported_honestly(self):
        """Natural has no send, so Space cannot do anything — say so."""
        _, report = apply_macros(build_graph("natural", "bold"), {"space": 100})
        assert "space" in report.inert

    def test_macros_cannot_escape_safe_ranges(self):
        """The registry clamp is the backstop, not the macro's own arithmetic."""
        from src.dsp_engine.graph import render_graph
        audio, sr = sf.read(FIXTURE, dtype="float32")
        extreme = {n: 100.0 for n in MACRO_NAMES}
        adjusted, _ = apply_macros(build_graph("rescue", "extreme"), extreme)
        out = render_graph(audio, int(sr), adjusted)
        assert np.all(np.isfinite(out))

    def test_parse_ignores_junk(self):
        assert parse_macros(None) == {}
        assert parse_macros("not json") == {}
        assert parse_macros(json.dumps({"evil": 1, "body": 70})) == {"body": 70.0}

    def test_parse_clamps_out_of_range(self):
        parsed = parse_macros(json.dumps({"body": 500, "space": -20}))
        assert parsed == {"body": 100.0, "space": 0.0}
