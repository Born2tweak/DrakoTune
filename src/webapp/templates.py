"""Server-rendered, accessible HTML for the web skeleton (M14).

Audio-first: the before/after players lead the result page. Findings are
scannable with confidence badges; blockers and failures are announced clearly
(role="alert"). Layout is responsive (viewport + grid that stacks on mobile) and
keyboard-friendly (skip link, visible focus, native audio controls).
"""

import html

BRAND_TAGLINE = "explainable vocal cleanup — not a professional mix"

CSS = """
:root{--bg:#0f1115;--panel:#191d24;--text:#e8ebf0;--muted:#9aa4b2;--line:#2a2f38;
--accent:#5b8cff;--ok:#3fb96b;--warn:#e0a83d;--bad:#e5556e;--low:#6b7280;}
@media (prefers-color-scheme:light){:root{--bg:#f6f7f9;--panel:#fff;--text:#161a20;
--muted:#5b6472;--line:#e2e6ec;}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--accent)}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:var(--panel);
padding:8px;border-radius:6px;z-index:10}
header{display:flex;gap:10px;align-items:baseline;padding:16px 20px;border-bottom:1px solid var(--line)}
.brand{font-weight:700;font-size:1.2rem}.tag{color:var(--muted);font-size:.9rem}
main{max-width:860px;margin:0 auto;padding:20px}
h1{font-size:1.4rem;margin:.2em 0}h2{font-size:1.1rem;margin:1.4em 0 .5em;border-bottom:1px solid var(--line);padding-bottom:4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin:12px 0}
.ab{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media (max-width:600px){.ab{grid-template-columns:1fr}}
.ab figure{margin:0}.ab figcaption{font-weight:600;margin-bottom:6px}
audio{width:100%}
.badge{display:inline-block;font-size:.72rem;font-weight:700;text-transform:uppercase;
letter-spacing:.03em;padding:2px 8px;border-radius:999px;color:#0b0d10}
.badge-high{background:var(--ok)}.badge-medium{background:var(--warn)}.badge-low{background:var(--low);color:#fff}
ul.clean{list-style:none;padding:0;margin:0}ul.clean li{padding:6px 0;border-bottom:1px solid var(--line)}
ul.clean li:last-child{border-bottom:0}
.muted{color:var(--muted)}.pass{color:var(--ok)}.fail{color:var(--bad)}
.banner{border-radius:12px;padding:14px 16px;margin:12px 0;font-weight:600}
.banner-block{background:rgba(229,85,110,.15);border:1px solid var(--bad)}
.banner-warn{background:rgba(224,168,61,.15);border:1px solid var(--warn)}
.hint{color:var(--muted);font-size:.9rem}
button,input[type=file]{font:inherit}
button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:10px 16px;cursor:pointer}
:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
form.upload{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
"""


def page(title: str, body: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
        '<a class="skip" href="#main">Skip to content</a>'
        f'<header><span class="brand">DrakoTune</span>'
        f'<span class="tag">{html.escape(BRAND_TAGLINE)}</span></header>'
        f'<main id="main">{body}</main>'
        '<footer style="max-width:860px;margin:0 auto;padding:20px;color:var(--muted);'
        'border-top:1px solid var(--line);font-size:.9rem">'
        '<a href="/">Home</a> · <a href="/privacy">Privacy</a> · '
        "DrakoTune is not a professional mix or mastering engineer.</footer>"
        "</body></html>"
    )


def render_upload() -> str:
    return (
        "<h1>Clean up a raw vocal</h1>"
        '<p class="hint">Upload a WAV or MP3. DrakoTune diagnoses the recording, '
        "applies conservative processing, and shows a before/after you can compare "
        "and an explanation you can inspect.</p>"
        '<div class="card"><form class="upload" action="/upload" method="post" '
        'enctype="multipart/form-data">'
        '<label for="file">Vocal file</label>'
        '<input id="file" type="file" name="file" accept="audio/*" required '
        'aria-describedby="fhint">'
        '<button type="submit">Analyze</button>'
        '<span id="fhint" class="hint">Your audio stays private.</span>'
        "</form></div>"
        '<div class="card"><h2>What this is — and isn\'t</h2>'
        '<ul class="clean">'
        "<li>It <strong>diagnoses</strong> a raw vocal and applies conservative, "
        "explained processing.</li>"
        "<li>It shows a <strong>before/after</strong> and every decision, with limits.</li>"
        '<li class="muted">It is <strong>not</strong> a professional mix, mastering, '
        "pitch-correction, or an “AI makes it better” button.</li>"
        "</ul>"
        '<p class="hint">Pilot software — results are experimental. See '
        '<a href="/privacy">Privacy</a>.</p></div>'
    )


def render_privacy() -> str:
    return (
        "<h1>Privacy (pilot draft)</h1>"
        '<div class="card"><ul class="clean">'
        "<li>Your uploaded audio is treated as private creative material.</li>"
        "<li>Processing runs on our server; audio is <strong>not</strong> sent to any "
        "third-party service.</li>"
        "<li>Playback links are signed and time-limited; there are no public audio URLs.</li>"
        "<li>Working files are deleted on request and after a short retention window.</li>"
        "<li>We do not ask for personal information. Optional feedback is stored without audio.</li>"
        "<li>This is an early pilot draft, not a final legal policy.</li>"
        "</ul></div>"
        '<p><a href="/">Back</a></p>'
    )


def _confidence_class(text: str) -> str | None:
    low = text.lower()
    if "high confidence" in low:
        return "high"
    if "medium confidence" in low:
        return "medium"
    if "low confidence" in low:
        return "low"
    return None


def _finding_li(text: str) -> str:
    band = _confidence_class(text)
    safe = html.escape(text)
    if band:
        return f'<li>{safe} <span class="badge badge-{band}">{band}</span></li>'
    return f"<li>{safe}</li>"


def _players(job, before_src: str, after_src: str) -> str:
    return (
        '<h2>Before / After</h2>'
        '<p class="hint">Tab to a player and press Space to play. Compare the '
        "original against the processed version.</p>"
        '<div class="ab">'
        f'<figure><figcaption>Original</figcaption>'
        f'<audio controls preload="none" src="{before_src}" '
        'aria-label="Original vocal"></audio></figure>'
        f'<figure><figcaption>Processed</figcaption>'
        f'<audio controls preload="none" src="{after_src}" '
        'aria-label="Processed vocal"></audio></figure>'
        "</div>"
    )


def render_result(job, before_src: str, after_src: str | None) -> str:
    name = html.escape(job.name)

    if job.status != "completed":
        klass = "banner-block" if job.status == "failed" else "banner-warn"
        body = (
            f"<h1>{name}</h1>"
            f'<div class="banner {klass}" role="alert">Status: {html.escape(job.status)} — '
            f"{html.escape(job.message)}</div>"
        )
        if before_src:
            body += _players(job, before_src, before_src)
        body += '<p><a href="/">Try another file</a></p>'
        return body

    report = job.report
    evaluation = job.evaluation

    body = [f"<h1>{name}</h1>"]
    if job.blocked_targets:
        body.append(
            '<div class="banner banner-warn" role="alert">Enhancement limited for safety: '
            f"{html.escape(', '.join(job.blocked_targets))}. Only safe moves were applied.</div>"
        )
    body.append(_players(job, before_src, after_src or before_src))

    findings = "".join(_finding_li(f) for f in report.findings) or "<li>none</li>"
    body.append(f'<h2>Findings</h2><div class="card"><ul class="clean">{findings}</ul></div>')

    applied = [a for a in report.actions if a.startswith("applied ")]
    skipped = [a for a in report.actions if a.startswith("skipped ")]
    actions_html = "".join(f"<li>{html.escape(a)}</li>" for a in applied) or "<li>none</li>"
    skipped_html = "".join(
        f'<li class="muted">{html.escape(a)}</li>' for a in skipped
    )
    body.append(
        f'<h2>What DrakoTune did</h2><div class="card"><ul class="clean">{actions_html}'
        f"{skipped_html}</ul></div>"
    )

    ev_items = [
        f'<li>loudness change: {evaluation.deltas.get("loudness_gain_db", 0.0):+.2f} dB</li>'
    ]
    ev_items += [f'<li class="pass">✓ {html.escape(c)}</li>' for c in evaluation.passed_checks]
    ev_items += [f'<li class="fail">✗ {html.escape(c)}</li>' for c in evaluation.failed_checks]
    for w in evaluation.warnings:
        ev_items.append(f'<li class="fail">! {html.escape(w)}</li>')
    body.append(
        f'<h2>Evaluation</h2><div class="card"><ul class="clean">{"".join(ev_items)}</ul></div>'
    )

    lims = "".join(f"<li>{html.escape(x)}</li>" for x in report.limitations)
    body.append(
        f'<h2>Limitations</h2><div class="card"><ul class="clean muted">{lims}</ul></div>'
    )

    body.append(
        '<h2>Feedback</h2><div class="card">'
        '<form action="/feedback" method="post">'
        f'<input type="hidden" name="job_id" value="{html.escape(job.id)}">'
        '<p><label for="rating">Was this helpful?</label> '
        '<select id="rating" name="rating">'
        '<option value="up">Yes</option><option value="down">No</option></select></p>'
        '<p><label for="comment">Comments (optional, no audio is sent)</label><br>'
        '<textarea id="comment" name="comment" rows="3" style="width:100%"></textarea></p>'
        "<button type=\"submit\">Send feedback</button></form></div>"
    )
    body.append('<p><a href="/">Try another file</a></p>')
    return "".join(body)
