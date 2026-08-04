/* DrakoTune workstation client (DT-97).
 *
 * A client-side app over the FastAPI JSON API. No framework and no build step:
 * the repo's CI enforces two-clean-environment SBOM parity over Python, and
 * pulling in an npm dependency tree would put a large part of the shipped
 * surface outside that gate. The API is plain JSON, so migrating to a framework
 * later costs nothing.
 *
 * The load-bearing piece is the A/B transport. Two <audio> elements would drift
 * apart and switching would restart playback, so both renders are decoded into
 * Web Audio buffers and played from one clock: switching swaps gain between two
 * sources that are already running in sample lock. The pair served is the
 * loudness-matched one, so a louder side cannot win on volume alone.
 */

const $ = (id) => document.getElementById(id);

/* Ceiling on a single request. It must cover BOTH the upload and the render:
 * a 67 MB take took 225 s to transfer alone on a ~3 Mbps connection, and a
 * full-length vocal then renders for a couple of minutes on top. Generous, but
 * finite, so a dead server surfaces as an error instead of an endless spinner. */
const UPLOAD_TIMEOUT_MS = 15 * 60 * 1000;

/* Learned from /api/modes, never hardcoded. Checking locally turns a
 * four-minute upload that ends in 413 into an instant, explainable refusal --
 * the server cannot answer until the whole body has arrived, even though it
 * knows the size from the first header. A previous hardcoded copy disagreed
 * with the deployed value and the mismatch was invisible from the browser.
 * The fallback only applies if discovery failed. */
let maxUploadMb = 50;
const api = {
  modes: () => fetch("/api/modes").then((r) => r.json()),
  /* XMLHttpRequest rather than fetch, because fetch cannot report upload
   * progress and on this material most of the wait IS the upload: a 67 MB take
   * measured 225 s on a ~3 Mbps connection. Showing "Processing…" for those
   * four minutes is why the app looked hung when it was working correctly.
   *
   * `onProgress` receives the fraction of the body sent, then null once the
   * server has it and is actually rendering. */
  upload: (form, onProgress) => new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/audio/upload");
    xhr.timeout = UPLOAD_TIMEOUT_MS;
    xhr.responseType = "text";

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total);
    };
    // Body fully sent: everything after this is server-side work.
    xhr.upload.onload = () => onProgress && onProgress(null);

    xhr.onload = () => {
      let body = {};
      try { body = JSON.parse(xhr.responseText); } catch { /* non-JSON error page */ }
      if (xhr.status === 413) {
        return reject(new Error(
          `That file is too large. The limit is ${body.max_mb || "?"} MB.`));
      }
      if (xhr.status === 429) {
        return reject(new Error("Too many requests just now. Wait a moment and try again."));
      }
      if (xhr.status < 200 || xhr.status >= 300) {
        return reject(new Error(
          body.detail || body.error || `Upload failed (${xhr.status})`));
      }
      resolve(body);
    };
    xhr.onerror = () => reject(new Error(
      "The connection dropped before the server answered. Check your network and retry."));
    xhr.ontimeout = () => reject(new Error(
      "The server stopped responding. This usually means the file was too long " +
      "for it to finish. Try a shorter section."));
    xhr.send(form);
  }),
};

const state = {
  file: null,
  beatName: null,
  modes: [],
  intensities: [],
  mode: null,
  intensity: null,
  job: null,
  macros: {},
};

/* Human-language macros. Each maps to engine behaviour the user should not have
 * to name. They are collected here and sent as a mode/intensity revision; a
 * macro never invents a capability the chain does not have. */
const MACROS = [
  { key: "repair", name: "Repair", hint: "Clean up noise, hum and room" },
  { key: "smoothness", name: "Smoothness", hint: "Tame harsh, sharp and sibilant" },
  { key: "body", name: "Body", hint: "Weight and fullness" },
  { key: "clarity", name: "Clarity", hint: "Cut through, stay intelligible" },
  { key: "presence", name: "Presence", hint: "Forward and close" },
  { key: "space", name: "Space", hint: "Room and depth around the voice" },
];

/* ------------------------------------------------------------------ */
/* Synchronized A/B transport                                          */
/* ------------------------------------------------------------------ */
class ABTransport {
  constructor(onFrame) {
    this.ctx = null;
    this.buffers = { original: null, processed: null };
    this.sources = {};
    this.gains = {};
    this.side = "processed";
    this.playing = false;
    this.startedAt = 0;
    this.offset = 0;
    this.loop = false;
    this.onFrame = onFrame;
    this._raf = null;
  }

  async load(urls) {
    this.ctx = this.ctx || new (window.AudioContext || window.webkitAudioContext)();
    const fetchBuf = async (url) => {
      const res = await fetch(url);
      if (!res.ok) throw new Error("Could not load audio for comparison");
      return this.ctx.decodeAudioData(await res.arrayBuffer());
    };
    const [original, processed] = await Promise.all([
      fetchBuf(urls.original), fetchBuf(urls.processed),
    ]);
    this.buffers = { original, processed };
    this.offset = 0;
  }

  get duration() {
    return this.buffers.processed ? this.buffers.processed.duration : 0;
  }

  get position() {
    if (!this.playing) return this.offset;
    const t = this.offset + (this.ctx.currentTime - this.startedAt);
    return this.loop && this.duration ? t % this.duration : Math.min(t, this.duration);
  }

  _build(at) {
    // Both sides run; only gain differs. That is what makes the switch
    // instantaneous and keeps the two sides in sample lock.
    for (const side of ["original", "processed"]) {
      const src = this.ctx.createBufferSource();
      src.buffer = this.buffers[side];
      src.loop = this.loop;
      const gain = this.ctx.createGain();
      gain.gain.value = side === this.side ? 1 : 0;
      src.connect(gain).connect(this.ctx.destination);
      src.start(0, at);
      this.sources[side] = src;
      this.gains[side] = gain;
    }
  }

  _teardown() {
    for (const side of ["original", "processed"]) {
      const src = this.sources[side];
      if (src) { try { src.stop(); } catch { /* already stopped */ } src.disconnect(); }
    }
    this.sources = {};
    this.gains = {};
  }

  async play() {
    if (this.playing || !this.buffers.processed) return;
    if (this.ctx.state === "suspended") await this.ctx.resume();
    if (this.offset >= this.duration) this.offset = 0;
    this._build(this.offset);
    this.startedAt = this.ctx.currentTime;
    this.playing = true;
    this._tick();
  }

  pause() {
    if (!this.playing) return;
    this.offset = this.position;
    this._teardown();
    this.playing = false;
    cancelAnimationFrame(this._raf);
    this.onFrame(this.position, false);
  }

  async toggle() { return this.playing ? this.pause() : this.play(); }

  seek(seconds) {
    const target = Math.max(0, Math.min(seconds, this.duration));
    if (this.playing) {
      this._teardown();
      this.offset = target;
      this._build(target);
      this.startedAt = this.ctx.currentTime;
    } else {
      this.offset = target;
      this.onFrame(target, false);
    }
  }

  setSide(side) {
    this.side = side;
    // Short ramp rather than a hard jump: an instantaneous gain step is an
    // audible click, which would colour the comparison.
    for (const s of ["original", "processed"]) {
      const g = this.gains[s];
      if (!g) continue;
      const now = this.ctx.currentTime;
      g.gain.cancelScheduledValues(now);
      g.gain.setValueAtTime(g.gain.value, now);
      g.gain.linearRampToValueAtTime(s === side ? 1 : 0, now + 0.012);
    }
  }

  setLoop(on) {
    this.loop = on;
    for (const s of ["original", "processed"]) {
      if (this.sources[s]) this.sources[s].loop = on;
    }
  }

  _tick() {
    const step = () => {
      if (!this.playing) return;
      const pos = this.position;
      if (!this.loop && pos >= this.duration) { this.pause(); this.offset = 0; return; }
      this.onFrame(pos, true);
      this._raf = requestAnimationFrame(step);
    };
    this._raf = requestAnimationFrame(step);
  }
}

/* ------------------------------------------------------------------ */
/* Waveform                                                            */
/* ------------------------------------------------------------------ */
class Waveform {
  constructor(canvas) {
    this.canvas = canvas;
    this.peaks = null;
    this.progress = 0;
    window.addEventListener("resize", () => this.draw());
  }

  setBuffer(buffer) {
    const data = buffer.getChannelData(0);
    const buckets = 900;
    const size = Math.floor(data.length / buckets) || 1;
    const peaks = new Float32Array(buckets);
    for (let i = 0; i < buckets; i++) {
      let peak = 0;
      const start = i * size;
      for (let j = 0; j < size; j++) {
        const v = Math.abs(data[start + j] || 0);
        if (v > peak) peak = v;
      }
      peaks[i] = peak;
    }
    this.peaks = peaks;
    this.draw();
  }

  draw() {
    const c = this.canvas;
    if (!this.peaks) return;
    const dpr = window.devicePixelRatio || 1;
    const w = c.clientWidth;
    const h = c.height;
    c.width = w * dpr;
    c.style.height = `${h}px`;
    const ctx = c.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    const css = getComputedStyle(document.documentElement);
    const accent = css.getPropertyValue("--accent").trim() || "#ff6b3d";
    const muted = css.getPropertyValue("--line").trim() || "#272d38";

    const mid = h / 2;
    const bars = this.peaks.length;
    const bw = w / bars;
    const playedX = this.progress * w;

    for (let i = 0; i < bars; i++) {
      const x = i * bw;
      const amp = Math.max(this.peaks[i] * (h * 0.44), 1);
      ctx.fillStyle = x < playedX ? accent : muted;
      ctx.fillRect(x, mid - amp, Math.max(bw - 0.6, 0.6), amp * 2);
    }

    ctx.fillStyle = accent;
    ctx.fillRect(playedX - 1, 6, 2, h - 12);
  }

  setProgress(p) { this.progress = p; this.draw(); }
}

/* ------------------------------------------------------------------ */
/* App                                                                 */
/* ------------------------------------------------------------------ */
const wave = new Waveform($("wave"));
const transport = new ABTransport((pos, playing) => {
  const dur = transport.duration || 1;
  wave.setProgress(pos / dur);
  $("time").textContent = `${fmt(pos)} / ${fmt(transport.duration)}`;
  if (playing) setPlayIcon(true);
});

function fmt(s) {
  if (!isFinite(s)) return "0:00";
  const m = Math.floor(s / 60);
  return `${m}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
}

function setPlayIcon(playing) {
  const el = $("play").firstElementChild;
  el.className = playing ? "icon-pause" : "icon-play";
  $("play").setAttribute("aria-label", playing ? "Pause" : "Play");
}

function showError(msg) {
  const el = $("error");
  el.textContent = msg;
  el.hidden = false;
  setTimeout(() => { el.hidden = true; }, 8000);
}

function stage(name) {
  for (const s of ["upload", "mode", "work"]) {
    $(`stage-${s}`).hidden = s !== name;
  }
}

/* ---------- source selection ---------- */
function pickFile(file) {
  if (!file) return;
  state.file = file;
  $("picked-name").textContent = file.name;
  stage("mode");
}

$("drop").addEventListener("click", () => $("file").click());
$("drop").addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $("file").click(); }
});
$("file").addEventListener("change", (e) => pickFile(e.target.files[0]));
$("change-file").addEventListener("click", () => stage("upload"));

for (const evt of ["dragenter", "dragover"]) {
  $("drop").addEventListener(evt, (e) => { e.preventDefault(); $("drop").classList.add("over"); });
}
for (const evt of ["dragleave", "drop"]) {
  $("drop").addEventListener(evt, (e) => { e.preventDefault(); $("drop").classList.remove("over"); });
}
$("drop").addEventListener("drop", (e) => pickFile(e.dataTransfer.files[0]));

$("beat").addEventListener("change", (e) => {
  const f = e.target.files[0];
  state.beatName = f ? f.name : null;
  $("beat-name").textContent = f ? `${f.name} loaded` : "";
});

$("about-toggle").addEventListener("click", (e) => {
  const open = $("about").hidden;
  $("about").hidden = !open;
  e.target.setAttribute("aria-expanded", String(open));
});

/* ---------- modes ---------- */
async function loadModes() {
  try {
    const data = await api.modes();
    if (data.limits && data.limits.max_upload_mb) maxUploadMb = data.limits.max_upload_mb;
    state.modes = data.modes;
    state.intensities = data.intensities;
    state.mode = data.default_mode || data.modes[0].name;
    const spec = state.modes.find((m) => m.name === state.mode);
    state.intensity = spec ? spec.default_intensity : "bold";
    renderModes();
    renderIntensities();
  } catch {
    showError("Could not load processing modes. Is the server running?");
  }
}

function renderModes() {
  $("modes").innerHTML = "";
  for (const m of state.modes) {
    const btn = document.createElement("button");
    btn.className = `mode${m.name === state.mode ? " is-on" : ""}`;
    btn.innerHTML = `
      <div class="mode-title"></div>
      <div class="mode-summary"></div>
      <ul class="mode-caps"></ul>`;
    btn.querySelector(".mode-title").textContent = m.title;
    btn.querySelector(".mode-summary").textContent = m.summary;
    const ul = btn.querySelector(".mode-caps");
    for (const c of m.capabilities.slice(0, 5)) {
      const li = document.createElement("li");
      li.textContent = c;           // rendered verbatim: no invented copy
      ul.appendChild(li);
    }
    btn.addEventListener("click", () => {
      state.mode = m.name;
      state.intensity = m.default_intensity;
      renderModes();
      renderIntensities();
    });
    $("modes").appendChild(btn);
  }
}

function renderIntensities() {
  $("intensities").innerHTML = "";
  for (const i of state.intensities) {
    const btn = document.createElement("button");
    btn.className = `intensity${i === state.intensity ? " is-on" : ""}`;
    btn.textContent = i[0].toUpperCase() + i.slice(1);
    btn.setAttribute("role", "radio");
    btn.setAttribute("aria-checked", String(i === state.intensity));
    btn.addEventListener("click", () => { state.intensity = i; renderIntensities(); });
    $("intensities").appendChild(btn);
  }
}

/* ---------- macros ---------- */
function renderMacros() {
  $("macros").innerHTML = "";
  for (const m of MACROS) {
    if (!(m.key in state.macros)) state.macros[m.key] = 50;
    const el = document.createElement("div");
    el.className = "macro";
    el.innerHTML = `
      <div class="macro-head">
        <span class="macro-name"></span><span class="macro-val"></span>
      </div>
      <div class="macro-hint"></div>
      <input type="range" min="0" max="100" step="1">`;
    el.querySelector(".macro-name").textContent = m.name;
    el.querySelector(".macro-hint").textContent = m.hint;
    const val = el.querySelector(".macro-val");
    const range = el.querySelector("input");
    range.value = state.macros[m.key];
    range.setAttribute("aria-label", m.name);
    val.textContent = state.macros[m.key];
    range.addEventListener("input", () => {
      state.macros[m.key] = Number(range.value);
      val.textContent = range.value;
    });
    $("macros").appendChild(el);
  }
}

$("reset-macros").addEventListener("click", () => {
  for (const m of MACROS) state.macros[m.key] = 50;
  renderMacros();
});

/* ---------- processing ---------- */
async function process() {
  if (!state.file) return showError("Choose a vocal first.");

  // Refuse locally rather than after a long upload. The server returns 413 only
  // once the entire body has arrived, so without this the user waits minutes to
  // be told the file was never acceptable.
  const sizeMb = state.file.size / (1024 * 1024);
  if (sizeMb > maxUploadMb) {
    return showError(
      `That file is ${sizeMb.toFixed(0)} MB and the limit is ${maxUploadMb} MB. ` +
      "Exporting as 24-bit instead of 32-bit float roughly halves the size.");
  }

  stage("mode");
  $("stage-mode").hidden = true;
  $("busy").hidden = false;
  $("busy-text").textContent = sizeMb > 8 ? "Uploading… 0%" : "Processing…";

  const form = new FormData();
  form.append("file", state.file);
  form.append("mode", state.mode);
  form.append("intensity", state.intensity);
  // Macros ride along so a revision is one request, not a second workflow.
  form.append("macros", JSON.stringify(state.macros));

  try {
    const job = await api.upload(form, (fraction) => {
      // null means the body is fully sent and the server is now rendering.
      $("busy-text").textContent = fraction === null
        ? "Processing… this takes a couple of minutes on a full song."
        : `Uploading… ${Math.round(fraction * 100)}%`;
    });
    if (job.status !== "completed") {
      throw new Error(job.message || "Processing did not complete.");
    }
    state.job = job;
    await openWorkstation(job);
  } catch (err) {
    showError(err.message);
    $("stage-mode").hidden = false;
  } finally {
    $("busy").hidden = true;
  }
}

async function openWorkstation(job) {
  const urls = job.audio_urls || {};
  // Prefer the loudness-matched pair. Without it the comparison is biased, so
  // say so rather than quietly presenting an unfair A/B.
  const original = urls.before_preview || urls.before;
  const processed = urls.after_preview || urls.after;
  $("ab-note").textContent = job.previews_matched
    ? "Both sides are volume-matched, so you are comparing the sound and not the loudness."
    : "Volume matching was not possible for this file — one side may simply be louder.";

  await transport.load({ original, processed });
  wave.setBuffer(transport.buffers.processed);
  wave.setProgress(0);
  $("time").textContent = `0:00 / ${fmt(transport.duration)}`;
  $("mode-badge").textContent =
    `${job.mode || "auto"} · ${job.intensity || "default"}` +
    (job.channels === 2 ? " · stereo" : "");
  setPlayIcon(false);
  renderMacros();
  renderInspector(job);
  stage("work");
}

function renderInspector(job) {
  const rows = {
    job_id: job.job_id,
    mode: job.mode,
    intensity: job.intensity,
    channels: job.channels,
    status: job.status,
    objectives: job.objectives,
    warnings: job.warnings,
    previews_loudness_matched: job.previews_matched,
    gain_staging: job.gain_staging,
    delivered_file: job.delivery,
  };
  $("inspector-body").innerHTML =
    "<h4>Run</h4><pre></pre><h4>Note</h4>" +
    "<pre>Measurements describe what changed. They are not evidence that it " +
    "sounds better — that judgement is yours.\n\n" +
    "delivered_file reports the exported audio: peak, true peak, integrated " +
    "loudness, crest factor, and (for stereo) channel correlation and what " +
    "summing to mono costs. A consistent peak is not consistent loudness, and " +
    "none of these numbers is a quality score.</pre>";
  $("inspector-body").querySelector("pre").textContent = JSON.stringify(rows, null, 2);
}

/* ---------- transport wiring ---------- */
$("go").addEventListener("click", process);
$("reapply").addEventListener("click", () => { transport.pause(); process(); });

// Test hook: browser end-to-end checks need to assert transport state, which is
// otherwise closed over. Read-only and namespaced.
window.__drakotune = { transport, state, wave };
$("play").addEventListener("click", async () => {
  // play() is async (it may need to resume a suspended context), so the icon
  // must be set after it settles — reading `playing` synchronously here would
  // always report the pre-click state.
  await transport.toggle();
  setPlayIcon(transport.playing);
});
$("loop").addEventListener("change", (e) => transport.setLoop(e.target.checked));

for (const [id, side] of [["ab-original", "original"], ["ab-processed", "processed"]]) {
  $(id).addEventListener("click", () => {
    transport.setSide(side);
    for (const other of ["ab-original", "ab-processed"]) {
      const on = other === id;
      $(other).classList.toggle("is-on", on);
      $(other).setAttribute("aria-pressed", String(on));
    }
  });
}

$("wave").addEventListener("click", (e) => {
  const rect = $("wave").getBoundingClientRect();
  transport.seek(((e.clientX - rect.left) / rect.width) * transport.duration);
});

document.addEventListener("keydown", async (e) => {
  if ($("stage-work").hidden) return;
  const typing = ["INPUT", "TEXTAREA"].includes(document.activeElement.tagName);
  if (e.code === "Space" && !typing) {
    e.preventDefault();
    await transport.toggle();
    setPlayIcon(transport.playing);
  }
  if (e.key.toLowerCase() === "a" && !typing) $("ab-original").click();
  if (e.key.toLowerCase() === "b" && !typing) $("ab-processed").click();
});

/* ---------- export ---------- */
function download(url, name) {
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

$("export").addEventListener("click", () => {
  const url = (state.job.audio_urls || {}).after;
  if (!url) return showError("Nothing to export yet.");
  download(url, `drakotune-${state.job.mode || "processed"}.wav`);
});
$("export-original").addEventListener("click", () => {
  const url = (state.job.audio_urls || {}).before;
  if (url) download(url, "original.wav");
});
$("restart").addEventListener("click", () => {
  transport.pause();
  state.file = null;
  state.job = null;
  $("file").value = "";
  stage("upload");
});

loadModes();
