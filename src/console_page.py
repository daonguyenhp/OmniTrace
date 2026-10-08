"""Single-page console shipped inside the package."""

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>OmniTrace</title>
<script>
(function () {
  try {
    var saved = localStorage.getItem("omnitrace-theme");
    var theme = saved || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
  } catch (err) {
    document.documentElement.setAttribute("data-theme", "light");
  }
})();
</script>
<style>
  html[data-theme="light"] {
    color-scheme: light;
    --bg: #efece6;
    --surface: #f7f5f1;
    --surface-2: #fffdf9;
    --ink: #1c1b18;
    --muted: #5e5952;
    --line: #ddd6cb;
    --line-strong: #c9c1b4;
    --accent: #1c1b18;
    --accent-ink: #f7f5f1;
    --fault: #8c2f2a;
    --fault-bg: #f6ebe8;
    --symptom: #7a5420;
    --symptom-bg: #f4efe4;
    --ok: #1d6b45;
    --select: #e8e2d8;
    --code: #2c3a30;
    --wash: rgba(140, 47, 42, 0.13);
    --shadow: 0 18px 50px rgba(28, 27, 24, 0.08);
  }
  html[data-theme="dark"] {
    color-scheme: dark;
    --bg: #14161a;
    --surface: #1c1f24;
    --surface-2: #23272d;
    --ink: #eceae4;
    --muted: #a8a295;
    --line: #31363d;
    --line-strong: #454c55;
    --accent: #eceae4;
    --accent-ink: #14161a;
    --fault: #e7a19b;
    --fault-bg: #2c211f;
    --symptom: #e4c891;
    --symptom-bg: #2b261c;
    --ok: #8fceb0;
    --select: #2a3038;
    --code: #d5dccf;
    --wash: rgba(231, 161, 155, 0.16);
    --shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--bg);
    color: var(--ink);
    font: 14px/1.45 "Segoe UI", system-ui, sans-serif;
  }
  button, a, input { font: inherit; color: inherit; }
  [hidden] { display: none !important; }
  :focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
  .home {
    flex: 1;
    width: 100%;
    margin: 0;
    padding: 36px 0 48px;
    background:
      radial-gradient(ellipse 55% 70% at 78% 42%, var(--wash), transparent 70%),
      var(--bg);
  }
  .home-inner {
    width: min(1080px, calc(100% - 48px));
    margin: 0 auto;
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(280px, 460px);
    gap: 48px;
    align-items: center;
  }
  .kicker {
    margin: 0 0 12px;
    color: var(--fault);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }
  .home h1 {
    margin: 0 0 16px;
    font-size: 58px;
    line-height: 0.98;
    font-weight: 650;
    letter-spacing: -0.035em;
  }
  .home p { margin: 0; font-size: 17px; line-height: 1.55; }
  .home .lead { color: var(--muted); max-width: 28em; }
  #start { margin-top: 26px; padding: 11px 22px; font-size: 15px; }
  .home-video {
    width: min(1080px, calc(100% - 48px));
    margin: 56px auto 0;
  }
  .home-video .kicker { margin-bottom: 12px; font-size: 12px; }
  .poster {
    margin: 0;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 16px 16px 8px;
    box-shadow: var(--shadow);
  }
  .poster svg { display: block; width: 100%; height: auto; }
  .poster .rail { stroke: var(--line-strong); stroke-width: 1.5; }
  .poster .dot { fill: var(--line-strong); }
  .poster .dot.hot { fill: var(--fault); }
  .poster .dot.warn { fill: var(--symptom); }
  .poster .bar { fill: var(--surface-2); stroke: var(--line-strong); }
  .poster .bar.bad { fill: var(--fault-bg); stroke: var(--fault); }
  .poster .bar.warn { fill: var(--symptom-bg); stroke: var(--symptom); }
  .poster .fork { fill: none; stroke: var(--fault); stroke-width: 1.6; }
  .poster .cap { fill: var(--muted); font: 13px "Segoe UI", system-ui, sans-serif; }
  .poster .cap.hot { fill: var(--fault); font-weight: 650; }
  .poster .cap.warn { fill: var(--symptom); }
  .site {
    position: sticky;
    top: 0;
    z-index: 2;
    background: var(--surface);
    border-bottom: 1px solid var(--line);
  }
  .nav, .site-foot {
    width: min(1180px, calc(100% - 32px));
    margin: 0 auto;
  }
  .nav {
    display: flex;
    align-items: stretch;
    gap: 18px;
    min-height: 52px;
  }
  .brand {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    text-decoration: none;
    border: 0;
    padding: 0;
    background: transparent;
    font-weight: 700;
    letter-spacing: 0.01em;
    flex-shrink: 0;
  }
  .brand:hover { background: transparent; }
  .mark {
    width: 22px;
    height: 22px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--ink);
    border-radius: 3px;
    font-size: 11px;
    font-weight: 700;
  }
  .menu { display: flex; align-items: stretch; gap: 2px; }
  .menu a {
    display: inline-flex;
    align-items: center;
    text-decoration: none;
    border: 0;
    border-bottom: 2px solid transparent;
    background: transparent;
    color: var(--muted);
    padding: 0 10px;
    margin-bottom: -1px;
    border-radius: 0;
  }
  .menu a:hover { color: var(--ink); background: transparent; }
  .menu a[aria-current="page"] {
    color: var(--ink);
    border-bottom-color: var(--ink);
  }
  .nav-end { display: flex; align-items: center; gap: 12px; margin-left: auto; flex-shrink: 0; }
  .local { color: var(--muted); font-size: 12px; }
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 16px;
    padding: 16px 0 14px;
  }
  .toolbar h1 { margin: 0; font-size: 22px; font-weight: 650; }
  .tagline { margin: 4px 0 0; color: var(--muted); font-size: 13px; }
  .bar-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
  button, .link {
    border: 1px solid var(--line-strong);
    background: transparent;
    border-radius: 4px;
    padding: 6px 11px;
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
  button:hover, .link:hover { background: var(--select); }
  button.primary:not(:disabled) {
    background: var(--accent);
    color: var(--accent-ink);
    border-color: var(--accent);
  }
  button.primary:not(:disabled):hover { filter: brightness(1.08); }
  button:disabled { opacity: 0.38; cursor: default; }
  .theme {
    display: flex;
    border: 1px solid var(--line-strong);
    border-radius: 4px;
    overflow: hidden;
  }
  .theme button { border: 0; border-radius: 0; padding: 6px 10px; }
  .theme button + button { border-left: 1px solid var(--line-strong); }
  .theme button[aria-pressed="true"] {
    background: var(--ink);
    color: var(--bg);
  }
  main {
    flex: 1;
    width: min(1100px, calc(100% - 40px));
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 20px 0 32px;
  }
  .home, #workbench { animation: rise 180ms ease; }
  @keyframes rise {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: none; }
  }
  button, .link { transition: background 120ms ease, border-color 120ms ease; }
  .intake-grid, .run-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 28px;
  }
  .work-bar, .run-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 16px;
  }
  .work-bar { margin-bottom: 14px; align-items: center; }
  .work-title { margin: 0; font-size: 15px; font-weight: 650; }
  .run-head {
    margin-bottom: 16px;
  }
  .run-head h2 { margin-bottom: 4px; }
  #run { position: relative; scroll-margin-top: 72px; }
  #close-run {
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 1;
    width: 28px;
    height: 28px;
    padding: 0;
    border: 0;
    background: transparent;
    color: var(--muted);
    font-size: 20px;
    line-height: 1;
  }
  #close-run:hover { color: var(--ink); background: var(--select); }
  .run-head { padding-right: 28px; }
  .samples {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
  }
  .sample {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 12px;
    border: 1px solid var(--line);
    border-radius: 6px;
    background: var(--surface-2);
  }
  .site-foot {
    display: grid;
    grid-template-columns: 1.4fr 1fr auto;
    gap: 18px;
    padding: 18px 0;
    border-top: 1px solid var(--line);
    color: var(--muted);
    font-size: 13px;
  }
  .site-foot strong { display: block; color: var(--ink); font-weight: 650; margin-bottom: 2px; }
  .site-foot p { margin: 0; }
  section {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 14px;
  }
  h2 {
    margin: 0 0 10px;
    font-size: 12px;
    font-weight: 650;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .drop {
    border: 1px dashed var(--line-strong);
    border-radius: 4px;
    padding: 14px;
    margin-bottom: 14px;
    background: var(--surface-2);
  }
  .drop.hot { border-style: solid; border-color: var(--ink); }
  .drop strong { display: block; font-weight: 650; margin-bottom: 2px; }
  .drop .hint { color: var(--muted); font-size: 13px; }
  .file-name {
    margin-top: 8px;
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 12px;
    color: var(--ink);
  }
  .file-name:empty { display: none; }
  #pick { margin-top: 10px; }
  .sample-title { font-weight: 600; }
  .sample-actions { display: flex; gap: 6px; }
  .meta, .hint, ol.guide { color: var(--muted); }
  .meta { font-family: Consolas, "Cascadia Mono", monospace; font-size: 12px; }
  ol.guide { margin: 12px 0 0; padding-left: 18px; font-size: 13px; }
  ol.guide li { margin-bottom: 8px; }
  .video-slot {
    border: 1px dashed var(--line-strong);
    border-radius: 10px;
    aspect-ratio: 16 / 9;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    text-align: center;
    background: var(--surface);
    color: var(--muted);
    font-size: 15px;
  }
  #guide-video {
    display: block;
    width: 100%;
    border-radius: 10px;
    background: #111;
    aspect-ratio: 16 / 9;
  }
  code {
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 12px;
    color: var(--code);
  }
  .step {
    width: 100%;
    text-align: left;
    margin: 0 0 6px;
    padding: 8px 10px;
    border-color: var(--line);
    background: var(--surface-2);
    display: block;
  }
  .step.on { background: var(--select); box-shadow: inset 3px 0 0 var(--ink); }
  .step.flag { background: var(--symptom-bg); }
  .step.fault { background: var(--fault-bg); box-shadow: inset 3px 0 0 var(--fault); }
  .step .line { font-weight: 600; }
  .badge {
    display: inline-block;
    margin-left: 6px;
    padding: 0 6px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 650;
    letter-spacing: 0.04em;
    vertical-align: 1px;
  }
  .badge.flag { background: var(--symptom-bg); color: var(--symptom); border: 1px solid var(--symptom); }
  .badge.fault { background: var(--fault-bg); color: var(--fault); border: 1px solid var(--fault); }
  .msg {
    padding: 7px 10px;
    border-left: 3px solid var(--line-strong);
    margin: 0 0 6px;
    background: var(--surface-2);
  }
  .msg.poison { border-color: var(--fault); background: var(--fault-bg); }
  .card {
    border-top: 1px solid var(--line);
    padding: 12px 0 2px;
    margin-top: 4px;
  }
  .card:first-child { border-top: 0; margin-top: 0; padding-top: 0; }
  .card strong { display: block; margin-bottom: 4px; }
  .poison-text {
    color: var(--fault);
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 13px;
    white-space: pre-wrap;
    margin: 6px 0;
  }
  .ok { color: var(--ok); margin-top: 6px; }
  pre {
    white-space: pre-wrap;
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 12px;
    color: var(--muted);
    margin: 6px 0 0;
  }
  #samples, #guide { scroll-margin-top: 72px; }
  .err { color: var(--fault); }
  .split { margin-top: 16px; }
  input[type=file] { display: none; }
  @media (max-width: 1080px) {
    main, .site-foot, .intake-grid, .run-grid, .samples { grid-template-columns: 1fr; }
    .bar-actions { flex-wrap: wrap; }
    .home-inner { grid-template-columns: 1fr; gap: 28px; }
    .home h1 { font-size: 42px; }
  }
  @media (max-width: 640px) {
    .local { display: none; }
    .nav { gap: 8px; }
  }
</style>
</head>
<body>
<header class="site">
  <div class="nav-wrap">
  <div class="nav">
    <a class="brand" href="#home" id="nav-brand">
      <span class="mark">OT</span>
      OmniTrace
    </a>
    <nav class="menu" aria-label="Main">
      <a href="#home" id="nav-home" aria-current="page">Home</a>
      <a href="#workbench" id="nav-work" class="app-only" hidden>Workbench</a>
    </nav>
    <div class="nav-end">
      <span class="local">Runs on this machine</span>
      <div class="theme" role="group" aria-label="Color theme">
        <button type="button" id="theme-light" aria-pressed="false">Light</button>
        <button type="button" id="theme-dark" aria-pressed="false">Dark</button>
      </div>
    </div>
    </div>
  </div>
</header>
<div id="home" class="home">
  <div class="home-inner">
    <div>
      <p class="kicker">Debugger for an agent run</p>
      <h1>Pinpoint the<br>failing span.</h1>
      <p class="lead">Drop in the trace of a run that just failed. OmniTrace finds the smallest piece that still fails, then opens a new thread with that piece removed.</p>
      <button type="button" class="primary" id="start">Start</button>
    </div>
    <figure class="poster">
      <svg viewBox="0 0 480 340" role="img" aria-label="One run, the failing span marked, then a branch into a new thread.">
        <text class="cap" x="20" y="22">Old run</text>
        <line class="rail" x1="28" y1="40" x2="28" y2="250"/>
        <circle class="dot" cx="28" cy="58" r="4"/>
        <rect class="bar" x="48" y="42" width="150" height="32" rx="5"/>
        <text class="cap" x="62" y="63">01   intake</text>
        <circle class="dot hot" cx="28" cy="110" r="5"/>
        <rect class="bar bad" x="48" y="94" width="230" height="32" rx="5"/>
        <text class="cap hot" x="62" y="115">02   cause</text>
        <circle class="dot" cx="28" cy="162" r="4"/>
        <rect class="bar" x="48" y="146" width="128" height="32" rx="5"/>
        <text class="cap" x="62" y="167">03   plan</text>
        <circle class="dot warn" cx="28" cy="214" r="4"/>
        <rect class="bar warn" x="48" y="198" width="176" height="32" rx="5"/>
        <text class="cap warn" x="62" y="219">05   symptom</text>
        <path class="fork" d="M278 110 C 360 110, 360 168, 360 196"/>
        <text class="cap hot" x="332" y="188">New thread</text>
        <line class="rail" x1="360" y1="204" x2="360" y2="312"/>
        <circle class="dot hot" cx="360" cy="222" r="4"/>
        <rect class="bar" x="376" y="206" width="88" height="30" rx="5"/>
        <text class="cap" x="388" y="226">cleaned</text>
        <circle class="dot" cx="360" cy="272" r="4"/>
        <rect class="bar" x="376" y="256" width="84" height="30" rx="5"/>
        <text class="cap" x="388" y="276">resume</text>
      </svg>
    </figure>
  </div>
  <section class="home-video" aria-label="Tutorial">
    <p class="kicker">Tutorial</p>
    <video id="guide-video" controls playsinline hidden></video>
    <div id="guide-video-empty" class="video-slot">Add <code>examples/guide.mp4</code>, then refresh. The tutorial plays here.</div>
  </section>
</div>
<main id="workbench" hidden>
  <div class="work-bar">
    <p class="work-title">Workbench</p>
    <button type="button" id="close-work">Close</button>
  </div>
  <section>
    <div class="intake-grid">
      <div>
        <h2>Trace file</h2>
        <div class="drop" id="drop">
          <strong>Drop a trace file here</strong>
          <div class="hint">One .otlp.json file, one failed run.</div>
          <div class="file-name" id="file-name"></div>
          <button type="button" id="pick">Choose file</button>
          <input id="file" type="file" accept="application/json,.json,.otlp.json" />
        </div>
        <p id="intake-error" class="err" hidden></p>
      </div>
      <div id="guide">
        <h2>Get a file</h2>
        <p class="hint">Any agent can produce this file. It is one failed run, exported as OpenTelemetry JSON.</p>
        <ol class="guide">
          <li>Turn on GenAI tracing and export that run as JSON with <code>resourceSpans</code>.</li>
          <li>Each <code>chat</code> or <code>execute_tool</code> span is one step. <code>STATUS_CODE_ERROR</code> is where the failure showed up.</li>
          <li>Set <code>omnitrace.oracle.type</code> and <code>omnitrace.oracle.text</code> on the resource. If they are missing, the <code>exception</code> message is used when it appears inside a span.</li>
        </ol>
      </div>
    </div>
    <h2 class="split" id="samples">Or open a sample</h2>
    <div class="samples" id="sample-list"></div>
  </section>
  <section id="run" hidden>
    <button type="button" id="close-run" aria-label="Close this run">&times;</button>
    <div class="run-head">
      <div>
        <h2>This run</h2>
        <p class="empty" id="blurb">No file open yet.</p>
      </div>
      <div class="bar-actions">
        <button class="primary" id="isolate" disabled>Isolate</button>
        <button id="fork" disabled>Fork</button>
        <button id="inspect" disabled title="Runs GPT-2 on the machine that hosts this page. Needs: uv sync --extra interp">Inspect</button>
      </div>
    </div>
    <div class="run-grid">
      <div>
        <h2>Timeline</h2>
        <div id="timeline"><p class="empty">No trace yet.</p></div>
      </div>
      <div>
        <h2>Checkpoint</h2>
        <div id="detail"><p class="empty">Select a step on the timeline.</p></div>
        <h2 class="split">Result</h2>
        <div id="diagnosis"><p class="empty">Click Isolate.</p></div>
      </div>
    </div>
  </section>
</main>
<footer class="site-foot">
  <p><strong>OmniTrace</strong>A debugger for one agent run. The trace file stays on this machine.</p>
  <p><strong>Author</strong>Nguyễn Đăng Gia Đạo</p>
  <p>© 2026</p>
</footer>
<script>
const $ = (id) => document.getElementById(id);
let data = null;
let selected = null;

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  try { localStorage.setItem("omnitrace-theme", theme); } catch (err) {}
  $("theme-light").setAttribute("aria-pressed", theme === "light" ? "true" : "false");
  $("theme-dark").setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
}

function setBusy(on) {
  const ready = data && data.ran;
  $("isolate").disabled = on || !ready;
  $("fork").disabled = on || !ready;
  $("inspect").disabled = on || !ready;
  $("pick").disabled = on;
}

function showError(message) {
  const box = $("intake-error");
  box.hidden = false;
  box.textContent = message;
}

function clearError() {
  $("intake-error").hidden = true;
  $("intake-error").textContent = "";
}

async function post(path, payload) {
  setBusy(true);
  try {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body.error || "request failed");
    data = body;
    if (body.isolation) selected = body.isolation.fault_super_step;
    else if (body.steps && body.steps.length) {
      const flagged = body.steps.find((step) => step.flagged);
      selected = flagged ? flagged.super_step : body.steps[body.steps.length - 1].super_step;
    }
    clearError();
    const reveal = data.ran && $("run").hidden;
    if (data.ran) $("run").hidden = false;
    render();
    if (reveal) $("run").scrollIntoView({ behavior: "smooth", block: "start" });
    else if (body.inspect || body.fork || body.isolation) $("diagnosis").scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (err) {
    showError(err.message);
  } finally {
    setBusy(false);
  }
}

function oracleLabel(oracle) {
  if (!oracle) return "";
  if (oracle.type === "contains") return "Still fails while «" + oracle.text + "» remains.";
  if (oracle.type === "tool_repeat") return "Still fails if one tool is called more than " + oracle.limit + " times.";
  return "";
}

function render() {
  if (data && data.case) {
    const law = oracleLabel(data.case.oracle);
    $("blurb").textContent = data.case.title + ". " + data.case.summary + (law ? " " + law : "");
  }
  const timeline = $("timeline");
  timeline.innerHTML = "";
  if (!data || !data.steps.length) {
    timeline.innerHTML = '<p class="empty">No trace yet.</p>';
    return;
  }
  const faultStep = data.isolation ? data.isolation.fault_super_step : null;
  for (const step of data.steps) {
    const btn = document.createElement("button");
    btn.className = "step";
    if (step.super_step === selected) btn.classList.add("on");
    if (step.flagged) btn.classList.add("flag");
    if (step.super_step === faultStep) btn.classList.add("fault");
    const title = step.messages.length ? step.messages[step.messages.length - 1].text : "empty";
    const line = document.createElement("div");
    line.className = "line";
    line.textContent = String(step.super_step).padStart(2, "0") + "  " + title;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = step.checkpoint_id;
    btn.append(line, meta);
    if (step.flagged) {
      const badge = document.createElement("span");
      badge.className = "badge flag";
      badge.textContent = "Symptom";
      line.append(badge);
    }
    if (step.super_step === faultStep) {
      const badge = document.createElement("span");
      badge.className = "badge fault";
      badge.textContent = "Cause";
      line.append(badge);
    }
    btn.onclick = () => { selected = step.super_step; render(); };
    timeline.append(btn);
  }
  renderDetail();
  renderDiagnosis();
}

function renderDetail() {
  const box = $("detail");
  const step = (data.steps || []).find((item) => item.super_step === selected);
  box.innerHTML = "";
  if (!step) {
    box.innerHTML = '<p class="empty">Select a step on the timeline.</p>';
    return;
  }
  const head = document.createElement("p");
  head.className = "meta";
  head.textContent = data.thread_id + "   " + step.checkpoint_id + "   parent " + (step.parent_checkpoint_id || "—");
  box.append(head);
  const fragments = (data.isolation && data.isolation.fragments) || [];
  for (const message of step.messages) {
    const row = document.createElement("p");
    const hot = fragments.includes(message.text) || (data.needle && message.text.includes(data.needle));
    row.className = "msg" + (hot ? " poison" : "");
    row.textContent = message.tool ? message.tool + "  " + message.text : message.text;
    box.append(row);
  }
}

function renderDiagnosis() {
  const box = $("diagnosis");
  box.innerHTML = "";
  if (!data.isolation && !data.fork && !data.inspect) {
    box.innerHTML = '<p class="empty">Click Isolate to get the smallest piece that still fails.</p>';
    return;
  }
  if (data.isolation) {
    const card = document.createElement("div");
    card.className = "card";
    const title = document.createElement("strong");
    const count = (data.isolation.fragments || []).length;
    title.textContent = "Failing piece  ·  " + count + " span" + (count === 1 ? "" : "s") + ", from step " + data.isolation.fault_super_step;
    const text = document.createElement("div");
    text.className = "poison-text";
    text.textContent = (data.isolation.fragments || [data.isolation.fragment]).join("\n");
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = "Symptom at step " + data.isolation.symptom_super_step
      + "   source " + data.isolation.fault_checkpoint_id
      + "   " + data.isolation.evals + " checks";
    card.append(title, text, meta);
    box.append(card);
  }
  if (data.fork) {
    const card = document.createElement("div");
    card.className = "card";
    const title = document.createElement("strong");
    title.textContent = "New thread  " + data.fork.new_thread_id;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = "From " + data.fork.parent_checkpoint_id
      + "   step " + data.fork.super_step
      + "   old thread still has " + data.fork.old_step_count + " steps";
    card.append(title, meta);
    for (const message of data.fork.messages) {
      const row = document.createElement("p");
      row.className = "msg";
      row.textContent = message.text;
      card.append(row);
    }
    const ok = document.createElement("div");
    ok.className = "ok";
    ok.textContent = "The new thread no longer contains the failing piece.";
    card.append(ok);
    box.append(card);
  }
  if (data.inspect) {
    const card = document.createElement("div");
    card.className = "card";
    const title = document.createElement("strong");
    title.textContent = data.inspect.ok ? "Inspect" : "Inspect did not run";
    const pre = document.createElement("pre");
    pre.textContent = data.inspect.text;
    card.append(title, pre);
    box.append(card);
  }
}

async function readTrace(file) {
  $("file-name").textContent = file.name;
  let payload;
  try {
    payload = JSON.parse(await file.text());
  } catch (err) {
    showError("File is not JSON: " + err.message);
    return;
  }
  post("/api/load", payload);
}

async function loadCatalog() {
  const res = await fetch("/api/cases");
  const body = await res.json();
  const box = $("sample-list");
  box.innerHTML = "";
  for (const item of body.cases) {
    const row = document.createElement("div");
    row.className = "sample";
    const label = document.createElement("div");
    const title = document.createElement("div");
    title.className = "sample-title";
    title.textContent = item.title;
    const file = document.createElement("div");
    file.className = "meta";
    file.textContent = item.id + ".otlp.json";
    label.append(title, file);
    const actions = document.createElement("div");
    actions.className = "sample-actions";
    const open = document.createElement("button");
    open.type = "button";
    open.textContent = "Open";
    open.setAttribute("aria-label", "Open " + item.id);
    open.onclick = () => openSample(item.id);
    const save = document.createElement("a");
    save.className = "link";
    save.href = "/api/sample/" + item.id;
    save.download = item.id + ".otlp.json";
    save.textContent = "Download";
    save.setAttribute("aria-label", "Download " + item.id);
    actions.append(open, save);
    row.append(label, actions);
    box.append(row);
  }
}

async function openSample(id) {
  setBusy(true);
  try {
    const res = await fetch("/api/sample/" + id);
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.error || "could not load the sample");
    $("file-name").textContent = id + ".otlp.json";
    setBusy(false);
    post("/api/load", payload);
  } catch (err) {
    $("intake-error").textContent = err.message;
    $("intake-error").hidden = false;
    setBusy(false);
  }
}

function showView(name) {
  const work = name === "work";
  $("home").hidden = work;
  $("workbench").hidden = !work;
  document.querySelectorAll(".app-only").forEach((item) => { item.hidden = !work; });
  if (work) {
    $("nav-home").removeAttribute("aria-current");
    $("nav-work").setAttribute("aria-current", "page");
  } else {
    $("nav-work").removeAttribute("aria-current");
    $("nav-home").setAttribute("aria-current", "page");
  }
  const next = work ? "#workbench" : "#home";
  if (location.hash !== next) history.replaceState(null, "", next);
  window.scrollTo(0, 0);
}

$("start").onclick = () => showView("work");
$("close-work").onclick = () => showView("home");
$("close-run").onclick = () => { $("run").hidden = true; };
$("nav-home").onclick = (event) => { event.preventDefault(); showView("home"); };
$("nav-brand").onclick = (event) => { event.preventDefault(); showView("home"); };
$("nav-work").onclick = (event) => { event.preventDefault(); showView("work"); };
if (location.hash === "#workbench" || location.hash === "#samples" || location.hash === "#guide") showView("work");

$("theme-light").onclick = () => applyTheme("light");
$("theme-dark").onclick = () => applyTheme("dark");
applyTheme(document.documentElement.getAttribute("data-theme") || "light");
$("isolate").onclick = () => post("/api/isolate");
$("fork").onclick = () => post("/api/fork");
$("inspect").onclick = () => post("/api/inspect");
$("pick").onclick = () => $("file").click();
$("file").onchange = () => {
  const file = $("file").files && $("file").files[0];
  if (file) readTrace(file);
};
const drop = $("drop");
drop.addEventListener("dragover", (event) => {
  event.preventDefault();
  drop.classList.add("hot");
});
drop.addEventListener("dragleave", () => drop.classList.remove("hot"));
drop.addEventListener("drop", (event) => {
  event.preventDefault();
  drop.classList.remove("hot");
  const file = event.dataTransfer.files && event.dataTransfer.files[0];
  if (file) readTrace(file);
});
loadCatalog();
loadGuideVideo();

async function loadGuideVideo() {
  const res = await fetch("/guide.mp4", { headers: { Range: "bytes=0-1" } });
  if (res.status !== 200 && res.status !== 206) return;
  $("guide-video").src = "/guide.mp4";
  $("guide-video").hidden = false;
  $("guide-video-empty").hidden = true;
}
</script>
</body>
</html>
"""
