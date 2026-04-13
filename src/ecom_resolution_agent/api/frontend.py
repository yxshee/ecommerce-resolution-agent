# ruff: noqa: E501
from __future__ import annotations


def render_dashboard_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Ecommerce Resolution Agent | Simulation Console</title>
  <meta name="description" content="Interactive simulation dashboard for the Ecommerce Resolution Agent multi-agent resolution system." />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #07121a;
      --panel: rgba(10, 21, 29, 0.76);
      --panel-strong: rgba(12, 25, 34, 0.92);
      --text: #ecf4f7;
      --muted: #9fb8bf;
      --line: rgba(188, 225, 235, 0.14);
      --teal: #35d1c4;
      --cyan: #77d6ff;
      --amber: #ffb657;
      --coral: #ff7a59;
      --lime: #a5eb78;
      --danger: #ff6b6b;
      --ok: #58df9d;
      --shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
      --radius: 18px;
      --mono: "IBM Plex Mono", "Menlo", "Consolas", monospace;
      --sans: "Space Grotesk", "Trebuchet MS", sans-serif;
    }

    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: var(--sans);
      color: var(--text);
      background:
        radial-gradient(circle at 12% 18%, rgba(53, 209, 196, 0.18), transparent 45%),
        radial-gradient(circle at 84% 10%, rgba(255, 182, 87, 0.16), transparent 44%),
        radial-gradient(circle at 70% 75%, rgba(119, 214, 255, 0.14), transparent 48%),
        linear-gradient(180deg, #051018 0%, #07121a 48%, #081722 100%);
      overflow-x: hidden;
    }

    body::before,
    body::after {
      content: "";
      position: fixed;
      width: 36rem;
      height: 36rem;
      border-radius: 50%;
      filter: blur(32px);
      opacity: 0.18;
      pointer-events: none;
      z-index: 0;
      animation: drift 18s ease-in-out infinite alternate;
    }

    body::before {
      top: -8rem;
      right: -8rem;
      background: conic-gradient(from 60deg, var(--coral), var(--amber), var(--teal), var(--coral));
    }

    body::after {
      left: -10rem;
      bottom: -12rem;
      background: conic-gradient(from 180deg, var(--cyan), var(--teal), var(--lime), var(--cyan));
      animation-duration: 24s;
    }

    @keyframes drift {
      from { transform: translate3d(0, 0, 0) rotate(0deg); }
      to { transform: translate3d(18px, -12px, 0) rotate(8deg); }
    }

    .app {
      position: relative;
      z-index: 1;
      width: min(1200px, calc(100% - 2rem));
      margin: 1.25rem auto 2.5rem;
      display: grid;
      gap: 1rem;
    }

    .hero {
      display: grid;
      gap: 1rem;
      grid-template-columns: 1.15fr 0.85fr;
      padding: 1.1rem;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(12, 24, 33, 0.88), rgba(8, 18, 25, 0.8));
      border-radius: 22px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(8px);
    }

    .hero-card {
      padding: 1rem;
      border-radius: 16px;
      border: 1px solid rgba(188, 225, 235, 0.10);
      background: linear-gradient(180deg, rgba(9, 19, 26, 0.9), rgba(8, 16, 23, 0.72));
    }

    .eyebrow {
      display: inline-flex;
      gap: 0.5rem;
      align-items: center;
      border: 1px solid rgba(119, 214, 255, 0.26);
      background: rgba(119, 214, 255, 0.08);
      color: #d7f4ff;
      padding: 0.35rem 0.6rem;
      border-radius: 999px;
      font-size: 0.78rem;
      letter-spacing: 0.03em;
      margin-bottom: 0.85rem;
    }

    h1 {
      margin: 0;
      font-size: clamp(1.55rem, 3vw, 2.5rem);
      line-height: 1.02;
      letter-spacing: -0.02em;
    }

    .lede {
      margin: 0.85rem 0 1.15rem;
      color: var(--muted);
      line-height: 1.45;
      max-width: 60ch;
    }

    .badge-row,
    .chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.55rem;
    }

    .badge,
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.02);
      padding: 0.35rem 0.65rem;
      font-size: 0.78rem;
      color: #e6f2f4;
    }

    .badge strong,
    .chip strong {
      font-weight: 600;
      color: var(--text);
    }

    .status-dot {
      width: 0.42rem;
      height: 0.42rem;
      border-radius: 50%;
      background: var(--ok);
      box-shadow: 0 0 0 5px rgba(88, 223, 157, 0.12);
      display: inline-block;
    }

    .hero-actions {
      margin-top: 1rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.65rem;
    }

    button,
    .link-btn {
      appearance: none;
      border: 1px solid transparent;
      border-radius: 12px;
      padding: 0.75rem 0.95rem;
      font: inherit;
      color: var(--text);
      cursor: pointer;
      transition: transform 0.12s ease, box-shadow 0.15s ease, border-color 0.15s ease, background 0.15s ease;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
    }

    button:hover,
    .link-btn:hover { transform: translateY(-1px); }
    button:disabled { opacity: 0.65; cursor: wait; transform: none; }

    .btn-primary {
      background: linear-gradient(135deg, rgba(53, 209, 196, 0.18), rgba(119, 214, 255, 0.18));
      border-color: rgba(119, 214, 255, 0.25);
      box-shadow: 0 10px 24px rgba(53, 209, 196, 0.12);
    }

    .btn-secondary {
      background: rgba(255,255,255,0.03);
      border-color: var(--line);
    }

    .btn-accent {
      background: linear-gradient(135deg, rgba(255, 182, 87, 0.16), rgba(255, 122, 89, 0.16));
      border-color: rgba(255, 182, 87, 0.25);
      box-shadow: 0 10px 24px rgba(255, 122, 89, 0.12);
    }

    .mini-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.7rem;
      margin-top: 0.7rem;
    }

    .metric {
      border-radius: 14px;
      border: 1px solid rgba(188, 225, 235, 0.1);
      background: rgba(255,255,255,0.02);
      padding: 0.8rem;
    }

    .metric .k {
      font-family: var(--mono);
      color: var(--muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .metric .v {
      margin-top: 0.25rem;
      font-size: 1rem;
      font-weight: 700;
      line-height: 1.1;
      overflow-wrap: anywhere;
    }

    .layout {
      display: grid;
      grid-template-columns: 1.08fr 0.92fr;
      gap: 1rem;
    }

    .stack {
      display: grid;
      gap: 1rem;
    }

    .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      backdrop-filter: blur(8px);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 1rem;
    }

    .panel h2 {
      margin: 0;
      font-size: 1.02rem;
      letter-spacing: -0.01em;
    }

    .subtle {
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.4;
      margin-top: 0.35rem;
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
      margin-bottom: 0.9rem;
    }

    .mono { font-family: var(--mono); }
    .tiny { font-size: 0.75rem; color: var(--muted); }
    .hidden { display: none !important; }

    .pill {
      font-family: var(--mono);
      border-radius: 999px;
      padding: 0.24rem 0.55rem;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.02);
      font-size: 0.72rem;
      color: #d8ecf0;
    }

    .pill.ok { border-color: rgba(88, 223, 157, 0.35); color: #b9f5d2; }
    .pill.warn { border-color: rgba(255, 182, 87, 0.35); color: #ffd7a0; }
    .pill.bad { border-color: rgba(255, 107, 107, 0.35); color: #ffc4c4; }
    .pill.info { border-color: rgba(119, 214, 255, 0.35); color: #c8efff; }

    .status-strip {
      display: flex;
      gap: 0.55rem;
      align-items: center;
      flex-wrap: wrap;
      margin-top: 0.4rem;
    }

    form {
      display: grid;
      gap: 0.9rem;
    }

    .form-grid {
      display: grid;
      gap: 0.75rem;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .field {
      display: grid;
      gap: 0.35rem;
    }

    .field label {
      font-size: 0.78rem;
      color: #d0e6eb;
      letter-spacing: 0.02em;
    }

    input,
    textarea,
    select {
      width: 100%;
      border-radius: 12px;
      border: 1px solid rgba(188, 225, 235, 0.18);
      background: rgba(5, 13, 18, 0.7);
      color: var(--text);
      padding: 0.72rem 0.78rem;
      font: inherit;
      outline: none;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }

    textarea {
      resize: vertical;
      min-height: 90px;
      font-family: var(--sans);
    }

    input:focus,
    textarea:focus,
    select:focus {
      border-color: rgba(119, 214, 255, 0.45);
      box-shadow: 0 0 0 4px rgba(119, 214, 255, 0.12);
    }

    .form-footer {
      display: flex;
      gap: 0.65rem;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
    }

    .pipeline {
      display: grid;
      grid-template-columns: repeat(11, minmax(120px, 1fr));
      gap: 0.55rem;
      overflow-x: auto;
      padding-bottom: 0.2rem;
      scrollbar-width: thin;
    }

    .stage {
      min-width: 120px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.02);
      padding: 0.65rem;
      position: relative;
    }

    .stage::after {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      border: 1px solid transparent;
      pointer-events: none;
    }

    .stage .idx {
      color: var(--muted);
      font-family: var(--mono);
      font-size: 0.7rem;
    }

    .stage .nm {
      margin-top: 0.35rem;
      font-size: 0.8rem;
      line-height: 1.25;
    }

    .stage.active {
      background: linear-gradient(180deg, rgba(53, 209, 196, 0.1), rgba(119, 214, 255, 0.06));
      border-color: rgba(119, 214, 255, 0.28);
    }

    .stage.active::after {
      border-color: rgba(53, 209, 196, 0.22);
      box-shadow: inset 0 0 0 1px rgba(53, 209, 196, 0.15), 0 0 0 1px rgba(53, 209, 196, 0.1);
    }

    .stage.done .idx { color: #bcf4e6; }
    .stage.done { border-color: rgba(88, 223, 157, 0.18); }

    .key-grid {
      display: grid;
      gap: 0.65rem;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .key-card {
      padding: 0.8rem;
      border-radius: 14px;
      border: 1px solid rgba(188, 225, 235, 0.1);
      background: rgba(255,255,255,0.02);
    }

    .key-card h3 {
      margin: 0;
      font-size: 0.87rem;
      color: #dff2f5;
    }

    .key-card p {
      margin: 0.35rem 0 0;
      color: var(--muted);
      font-size: 0.82rem;
      line-height: 1.35;
    }

    .list {
      display: grid;
      gap: 0.45rem;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .list li {
      border-radius: 12px;
      border: 1px solid rgba(188, 225, 235, 0.08);
      background: rgba(255,255,255,0.02);
      padding: 0.65rem 0.75rem;
      display: grid;
      gap: 0.25rem;
    }

    .list .label {
      font-size: 0.76rem;
      color: var(--muted);
      font-family: var(--mono);
    }

    .list .value {
      font-size: 0.9rem;
      line-height: 1.3;
      overflow-wrap: anywhere;
    }

    details {
      border: 1px solid rgba(188, 225, 235, 0.08);
      border-radius: 12px;
      background: rgba(255,255,255,0.02);
      overflow: hidden;
    }

    summary {
      cursor: pointer;
      padding: 0.7rem 0.8rem;
      font-size: 0.84rem;
      color: #d9eef2;
      list-style: none;
      user-select: none;
    }

    summary::-webkit-details-marker { display: none; }
    summary::before {
      content: "+";
      display: inline-block;
      width: 1rem;
      color: var(--cyan);
      margin-right: 0.35rem;
      font-weight: 700;
    }
    details[open] summary::before { content: "−"; }

    pre {
      margin: 0;
      padding: 0.85rem;
      border-top: 1px solid rgba(188, 225, 235, 0.08);
      overflow: auto;
      max-height: 360px;
      font-family: var(--mono);
      font-size: 0.76rem;
      line-height: 1.45;
      color: #d8f3fb;
      background: rgba(3, 9, 12, 0.6);
    }

    .metrics-board {
      display: grid;
      gap: 0.6rem;
    }

    .metric-bar {
      border-radius: 12px;
      border: 1px solid rgba(188, 225, 235, 0.08);
      background: rgba(255,255,255,0.02);
      padding: 0.65rem;
    }

    .metric-bar-top {
      display: flex;
      justify-content: space-between;
      gap: 0.75rem;
      align-items: baseline;
      margin-bottom: 0.45rem;
    }

    .metric-bar-top .name {
      font-size: 0.78rem;
      color: #d9eef2;
      font-family: var(--mono);
      overflow-wrap: anywhere;
    }

    .metric-bar-top .val {
      font-size: 0.82rem;
      color: var(--muted);
      font-family: var(--mono);
    }

    .bar-track {
      height: 0.52rem;
      border-radius: 999px;
      background: rgba(255,255,255,0.05);
      overflow: hidden;
    }

    .bar-fill {
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, rgba(53, 209, 196, 0.85), rgba(119, 214, 255, 0.85));
      width: 0%;
      transition: width 0.5s ease;
    }

    .footnote {
      color: var(--muted);
      font-size: 0.79rem;
      line-height: 1.4;
    }

    .toast {
      position: fixed;
      right: 1rem;
      bottom: 1rem;
      max-width: min(440px, calc(100% - 2rem));
      padding: 0.85rem 0.95rem;
      border-radius: 14px;
      border: 1px solid rgba(188, 225, 235, 0.16);
      background: rgba(10, 23, 31, 0.92);
      box-shadow: var(--shadow);
      transform: translateY(10px);
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.16s ease, transform 0.16s ease;
      z-index: 10;
      backdrop-filter: blur(8px);
      font-size: 0.86rem;
    }

    .toast.show {
      opacity: 1;
      transform: translateY(0);
    }

    .toast.ok { border-color: rgba(88, 223, 157, 0.28); }
    .toast.warn { border-color: rgba(255, 182, 87, 0.28); }
    .toast.bad { border-color: rgba(255, 107, 107, 0.28); }

    .fade-in {
      animation: fadeInUp 0.35s ease both;
    }

    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 1024px) {
      .hero,
      .layout {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 760px) {
      .app { width: min(100%, calc(100% - 0.75rem)); margin-top: 0.5rem; }
      .hero, .panel { padding: 0.8rem; }
      .hero-card { padding: 0.8rem; }
      .mini-grid,
      .key-grid,
      .form-grid { grid-template-columns: 1fr; }
      .hero-actions { gap: 0.5rem; }
      button, .link-btn { width: 100%; justify-content: center; }
      .form-footer { align-items: stretch; }
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        animation: none !important;
        transition: none !important;
        scroll-behavior: auto !important;
      }
    }
  </style>
</head>
<body>
  <main class="app">
    <section class="hero fade-in">
      <div class="hero-card">
        <div class="eyebrow"><span class="status-dot"></span> Live Simulation Console</div>
        <h1>Ecommerce Resolution Agent</h1>
        <p class="lede">
          A multi-agent resolution system for ecommerce support with deterministic policy evaluation,
          risk gating, idempotent actions, QA verification, and auditable artifacts. This frontend lets you
          inspect the pipeline, run scenarios, and explore evaluation outcomes in-browser.
        </p>
        <div class="badge-row" id="heroBadges">
          <span class="badge"><strong>Orchestration:</strong> LangGraph</span>
          <span class="badge"><strong>Actions:</strong> Simulation-first</span>
          <span class="badge"><strong>Safety:</strong> Caps + Idempotency + Approval Gates</span>
          <span class="badge"><strong>Audit:</strong> Redacted Artifacts</span>
        </div>
        <div class="hero-actions">
          <button id="runDemoBtn" class="btn-primary" type="button">Run Delivered-Not-Received Demo</button>
          <button id="runEvalBtn" class="btn-accent" type="button">Run Mini Evaluation</button>
          <a class="link-btn btn-secondary" href="/docs" target="_blank" rel="noreferrer">Open API Docs</a>
          <a class="link-btn btn-secondary" href="/healthz" target="_blank" rel="noreferrer">Health JSON</a>
        </div>
      </div>
      <div class="hero-card">
        <div class="panel-header">
          <div>
            <h2>System Snapshot</h2>
            <div class="subtle">Live API metadata and operational flags from this deployment.</div>
          </div>
          <span id="metaStatus" class="pill info">loading…</span>
        </div>
        <div class="mini-grid" id="snapshotGrid">
          <div class="metric"><div class="k">Mode</div><div class="v" id="snapMode">—</div></div>
          <div class="metric"><div class="k">Health</div><div class="v" id="snapHealth">—</div></div>
          <div class="metric"><div class="k">Environment</div><div class="v" id="snapEnv">—</div></div>
          <div class="metric"><div class="k">Simulation</div><div class="v" id="snapSimulation">—</div></div>
        </div>
        <div class="status-strip" id="snapshotChips"></div>
        <div class="subtle" style="margin-top:0.8rem">
          Tip: this page drives the same FastAPI endpoints available in Swagger. Try the demo run, then inspect artifacts and raw decision JSON below.
        </div>
      </div>
    </section>

    <section class="layout fade-in" style="animation-delay: 90ms">
      <div class="stack">
        <section class="panel" aria-labelledby="scenario-title">
          <div class="panel-header">
            <div>
              <h2 id="scenario-title">Scenario Runner</h2>
              <div class="subtle">Run a simulation case against the backend pipeline and inspect the selected resolution, QA outcome, and generated artifacts.</div>
            </div>
            <span id="runStatusPill" class="pill">idle</span>
          </div>

          <form id="scenarioForm">
            <div class="form-grid">
              <div class="field">
                <label for="ticketId">Ticket ID</label>
                <input id="ticketId" name="ticketId" value="ui_case_001" />
              </div>
              <div class="field">
                <label for="runId">Run ID (optional)</label>
                <input id="runId" name="runId" value="ui_demo_delivered_not_received" />
              </div>
              <div class="field">
                <label for="customerId">Customer ID</label>
                <input id="customerId" name="customerId" value="cus_001" />
              </div>
              <div class="field">
                <label for="orderId">Order ID</label>
                <input id="orderId" name="orderId" value="ord_001" />
              </div>
              <div class="field">
                <label for="customerEmail">Customer Email</label>
                <input id="customerEmail" name="customerEmail" type="email" value="alice@example.com" />
              </div>
              <div class="field">
                <label for="issueType">Issue Type</label>
                <select id="issueType" name="issueType">
                  <option value="delivered_not_received" selected>delivered_not_received</option>
                  <option value="order_status">order_status</option>
                  <option value="cancel_order">cancel_order</option>
                  <option value="return_request">return_request</option>
                  <option value="damaged_item">damaged_item</option>
                </select>
              </div>
            </div>

            <div class="field">
              <label for="customerMessage">Customer Message (untrusted input, QA injection checks apply)</label>
              <textarea id="customerMessage" name="customerMessage">The tracking says delivered, but the package never arrived at my door. Can you help?</textarea>
            </div>

            <div class="form-footer">
              <div class="chip-row">
                <span class="chip"><strong>Safety:</strong> Simulation only</span>
                <span class="chip"><strong>Execution:</strong> Mock tools</span>
                <span class="chip"><strong>Output:</strong> Audit artifacts + report</span>
              </div>
              <div class="hero-actions" style="margin-top:0">
                <button id="runCustomBtn" class="btn-primary" type="submit">Run Scenario</button>
                <button id="resetFormBtn" class="btn-secondary" type="button">Reset Sample</button>
              </div>
            </div>
          </form>
        </section>

        <section class="panel" aria-labelledby="pipeline-title">
          <div class="panel-header">
            <div>
              <h2 id="pipeline-title">Orchestration Pipeline</h2>
              <div class="subtle">Required state machine stages. The dashboard highlights the currently reported checkpoint and last run outcome.</div>
            </div>
            <span id="pipelineCheckpoint" class="pill info">waiting for run</span>
          </div>
          <div class="pipeline" id="pipelineStages"></div>
          <div class="subtle" style="margin-top:0.7rem">
            Rule examples enforced in the backend: identity-failure stop, policy disallow alternatives, risk escalation gate, safe action retry behavior with reconciliation checks.
          </div>
        </section>

        <section class="panel" aria-labelledby="result-title">
          <div class="panel-header">
            <div>
              <h2 id="result-title">Run Insights</h2>
              <div class="subtle">Decision, QA verification, action simulation result, and artifact inventory from the latest scenario run.</div>
            </div>
            <span id="decisionBadge" class="pill">no run yet</span>
          </div>

          <div class="key-grid" id="runInsightsGrid">
            <div class="key-card"><h3>Selected Action</h3><p id="selectedActionText">Run a case to inspect the chosen resolution path.</p></div>
            <div class="key-card"><h3>QA Outcome</h3><p id="qaOutcomeText">QA validation status will appear here.</p></div>
            <div class="key-card"><h3>Action Execution</h3><p id="actionOutcomeText">Simulation action status and idempotency-safe result will appear here.</p></div>
            <div class="key-card"><h3>Artifacts</h3><p id="artifactOutcomeText">Artifacts directory and generated files will appear after a run.</p></div>
          </div>

          <div style="margin-top:0.85rem" class="key-grid">
            <div>
              <h3 style="margin:0 0 0.45rem;font-size:0.87rem;color:#dff2f5">Artifact Files</h3>
              <ul class="list" id="artifactList">
                <li><span class="label">No run yet</span><span class="value">Run a scenario to generate and list audit/report artifacts.</span></li>
              </ul>
            </div>
            <div>
              <h3 style="margin:0 0 0.45rem;font-size:0.87rem;color:#dff2f5">Quick Facts</h3>
              <ul class="list" id="quickFactsList">
                <li><span class="label">Selected action</span><span class="value">—</span></li>
                <li><span class="label">QA approved</span><span class="value">—</span></li>
                <li><span class="label">Escalate to human</span><span class="value">—</span></li>
                <li><span class="label">Report path</span><span class="value">—</span></li>
              </ul>
            </div>
          </div>

          <div style="margin-top:0.85rem;display:grid;gap:0.65rem">
            <details>
              <summary>Latest Case Run Response (JSON)</summary>
              <pre id="caseRunJson">{\n  \"message\": \"No run yet\"\n}</pre>
            </details>
            <details>
              <summary>Latest Case Summary (JSON)</summary>
              <pre id="caseSummaryJson">{\n  \"message\": \"No summary yet\"\n}</pre>
            </details>
            <details>
              <summary>Latest Artifacts Listing (JSON)</summary>
              <pre id="artifactJson">{\n  \"message\": \"No artifacts yet\"\n}</pre>
            </details>
          </div>
        </section>
      </div>

      <div class="stack">
        <section class="panel" aria-labelledby="eval-title">
          <div class="panel-header">
            <div>
              <h2 id="eval-title">Evaluation Harness Snapshot</h2>
              <div class="subtle">Run a small batch from the synthetic scenario dataset to inspect reliability metrics and regression-gate outcomes.</div>
            </div>
            <span id="evalStatusPill" class="pill">idle</span>
          </div>

          <div class="form-grid">
            <div class="field">
              <label for="evalLimit">Scenario Limit</label>
              <input id="evalLimit" type="number" min="1" max="50" value="8" />
            </div>
            <div class="field">
              <label for="evalArtifacts">Write Scenario Artifacts</label>
              <select id="evalArtifacts">
                <option value="false" selected>false (faster)</option>
                <option value="true">true (store per-run bundles)</option>
              </select>
            </div>
          </div>

          <div class="hero-actions" style="margin-top:0.75rem">
            <button id="runEvalInlineBtn" class="btn-accent" type="button">Run Mini Eval</button>
          </div>

          <div style="margin-top:0.85rem" id="evalSummaryCards" class="mini-grid">
            <div class="metric"><div class="k">Scenarios</div><div class="v" id="evalScenarioCount">—</div></div>
            <div class="metric"><div class="k">Gate</div><div class="v" id="evalGateStatus">—</div></div>
            <div class="metric"><div class="k">Resolution Accuracy</div><div class="v" id="evalAccuracy">—</div></div>
            <div class="metric"><div class="k">Policy Compliance</div><div class="v" id="evalPolicyCompliance">—</div></div>
          </div>

          <div class="metrics-board" id="evalMetricsBoard" style="margin-top:0.85rem"></div>

          <details style="margin-top:0.85rem">
            <summary>Latest Evaluation Response (JSON)</summary>
            <pre id="evalJson">{\n  \"message\": \"No eval run yet\"\n}</pre>
          </details>
        </section>

        <section class="panel" aria-labelledby="safety-title">
          <div class="panel-header">
            <div>
              <h2 id="safety-title">Safety & Control Layer</h2>
              <div class="subtle">These controls are enforced in the backend before any real action execution is allowed.</div>
            </div>
            <span class="pill ok">guardrails active</span>
          </div>
          <ul class="list">
            <li>
              <span class="label">Least privilege tool access</span>
              <span class="value">`ToolExecutor` gates methods by agent role. Action tools remain simulation-first unless real actions are explicitly enabled.</span>
            </li>
            <li>
              <span class="label">Idempotency</span>
              <span class="value">Action requests derive stable keys from order/action/item/amount/policy and refuse duplicates through persisted action records.</span>
            </li>
            <li>
              <span class="label">Action caps</span>
              <span class="value">Per-run, per-customer/day, and per-order refund limits trigger approval or escalation depending on policy/risk.</span>
            </li>
            <li>
              <span class="label">Prompt injection defense</span>
              <span class="value">Customer text is untrusted. QA checks detect override attempts (e.g., “ignore policy”) and block unsafe auto actions.</span>
            </li>
            <li>
              <span class="label">PII redaction</span>
              <span class="value">Logs and audit bundles use centralized redaction for emails, phones, addresses, payment IDs, and other sensitive identifiers.</span>
            </li>
          </ul>
        </section>

        <section class="panel" aria-labelledby="architecture-title">
          <div class="panel-header">
            <div>
              <h2 id="architecture-title">What This Project Contains</h2>
              <div class="subtle">A quick map of the production-grade system components behind this interface.</div>
            </div>
            <span class="pill info">backend + eval + CLI + API</span>
          </div>
          <div class="key-grid">
            <div class="key-card"><h3>Multi-Agent Orchestration</h3><p>LangGraph state machine with explicit transitions from intake through reporting and audit persistence.</p></div>
            <div class="key-card"><h3>Policy Engine</h3><p>Versioned JSON policy rules with deterministic evaluation, constraints, required evidence, and approval flags.</p></div>
            <div class="key-card"><h3>Tooling Layer</h3><p>Strict Pydantic schemas, mock adapters for offline runs, and capability-gated tool execution with audit hooks.</p></div>
            <div class="key-card"><h3>Observability & Artifacts</h3><p>Structured logs, traces, redacted audit events, decision outputs, reports, and evaluation results written per run.</p></div>
          </div>
          <div class="hero-actions" style="margin-top:0.9rem">
            <a class="link-btn btn-secondary" href="/docs" target="_blank" rel="noreferrer">Swagger UI</a>
            <a class="link-btn btn-secondary" href="/redoc" target="_blank" rel="noreferrer">ReDoc</a>
            <button id="copyMetaBtn" class="btn-secondary" type="button">Copy API Metadata JSON</button>
          </div>
        </section>
      </div>
    </section>
  </main>

  <div id="toast" class="toast" role="status" aria-live="polite"></div>

  <script>
    const state = {
      meta: null,
      health: null,
      lastRun: null,
      lastArtifacts: null,
      lastEval: null,
    };

    const pipelineStates = [
      "intake",
      "verify_identity",
      "gather_facts",
      "classify_issue",
      "policy_lookup",
      "risk_assessment",
      "propose_resolution",
      "verify_resolution",
      "execute_or_escalate",
      "finalize_report",
      "persist_audit",
    ];

    const els = {
      metaStatus: document.getElementById("metaStatus"),
      snapMode: document.getElementById("snapMode"),
      snapHealth: document.getElementById("snapHealth"),
      snapEnv: document.getElementById("snapEnv"),
      snapSimulation: document.getElementById("snapSimulation"),
      snapshotChips: document.getElementById("snapshotChips"),
      runDemoBtn: document.getElementById("runDemoBtn"),
      runEvalBtn: document.getElementById("runEvalBtn"),
      runEvalInlineBtn: document.getElementById("runEvalInlineBtn"),
      runStatusPill: document.getElementById("runStatusPill"),
      evalStatusPill: document.getElementById("evalStatusPill"),
      scenarioForm: document.getElementById("scenarioForm"),
      resetFormBtn: document.getElementById("resetFormBtn"),
      pipelineStages: document.getElementById("pipelineStages"),
      pipelineCheckpoint: document.getElementById("pipelineCheckpoint"),
      decisionBadge: document.getElementById("decisionBadge"),
      selectedActionText: document.getElementById("selectedActionText"),
      qaOutcomeText: document.getElementById("qaOutcomeText"),
      actionOutcomeText: document.getElementById("actionOutcomeText"),
      artifactOutcomeText: document.getElementById("artifactOutcomeText"),
      artifactList: document.getElementById("artifactList"),
      quickFactsList: document.getElementById("quickFactsList"),
      caseRunJson: document.getElementById("caseRunJson"),
      caseSummaryJson: document.getElementById("caseSummaryJson"),
      artifactJson: document.getElementById("artifactJson"),
      evalJson: document.getElementById("evalJson"),
      evalMetricsBoard: document.getElementById("evalMetricsBoard"),
      evalScenarioCount: document.getElementById("evalScenarioCount"),
      evalGateStatus: document.getElementById("evalGateStatus"),
      evalAccuracy: document.getElementById("evalAccuracy"),
      evalPolicyCompliance: document.getElementById("evalPolicyCompliance"),
      evalLimit: document.getElementById("evalLimit"),
      evalArtifacts: document.getElementById("evalArtifacts"),
      copyMetaBtn: document.getElementById("copyMetaBtn"),
      toast: document.getElementById("toast"),
      runCustomBtn: document.getElementById("runCustomBtn"),
    };

    function showToast(message, kind = "ok") {
      if (!els.toast) return;
      els.toast.textContent = message;
      els.toast.className = `toast show ${kind}`;
      clearTimeout(showToast._t);
      showToast._t = setTimeout(() => {
        els.toast.className = "toast";
      }, 2400);
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
      });
      const contentType = response.headers.get("content-type") || "";
      const body = contentType.includes("application/json") ? await response.json() : await response.text();
      if (!response.ok) {
        const detail = typeof body === "string" ? body : (body.detail || JSON.stringify(body));
        throw new Error(`${response.status} ${response.statusText}: ${detail}`);
      }
      return body;
    }

    function pretty(value) {
      return JSON.stringify(value, null, 2);
    }

    function setPre(el, value) {
      if (!el) return;
      el.textContent = typeof value === "string" ? value : pretty(value);
    }

    function setPill(el, text, kind = "") {
      if (!el) return;
      el.textContent = text;
      el.className = `pill${kind ? ` ${kind}` : ""}`;
    }

    function normalizeStatusKind(text) {
      const s = String(text || "").toLowerCase();
      if (s.includes("fail") || s.includes("error") || s.includes("reject") || s.includes("blocked")) return "bad";
      if (s.includes("pending") || s.includes("warn") || s.includes("review") || s.includes("risk")) return "warn";
      if (s.includes("ok") || s.includes("pass") || s.includes("approved") || s.includes("completed") || s.includes("simulated")) return "ok";
      return "info";
    }

    function asPercent(value) {
      if (typeof value !== "number" || Number.isNaN(value)) return "—";
      return `${(value * 100).toFixed(1)}%`;
    }

    function asNumber(value) {
      if (typeof value !== "number" || Number.isNaN(value)) return "—";
      return String(value);
    }

    function buildPipeline(statusLabel) {
      els.pipelineStages.innerHTML = "";
      const checkpoint = String(statusLabel || "").toLowerCase();
      const idx = pipelineStates.indexOf(checkpoint);
      pipelineStates.forEach((name, i) => {
        const card = document.createElement("div");
        card.className = "stage";
        if (idx >= 0 && i < idx) card.classList.add("done");
        if (idx >= 0 && i === idx) card.classList.add("active");
        card.innerHTML = `<div class=\"idx\">${String(i + 1).padStart(2, "0")}</div><div class=\"nm\">${name}</div>`;
        els.pipelineStages.appendChild(card);
      });
      setPill(els.pipelineCheckpoint, checkpoint || "waiting for run", checkpoint ? normalizeStatusKind(checkpoint) : "info");
    }

    function updateSnapshot() {
      const meta = state.meta || {};
      const health = state.health || {};
      els.snapMode.textContent = meta.mode || "—";
      els.snapHealth.textContent = health.status || meta.status || "—";
      els.snapEnv.textContent = health.app_env || "—";
      els.snapSimulation.textContent = typeof health.simulation_mode === "boolean" ? String(health.simulation_mode) : "—";
      els.snapshotChips.innerHTML = "";
      [
        ["Docs", meta.docs_url],
        ["Health", meta.health_url],
        ["Run Case", meta.run_case_endpoint],
        ["Eval", meta.eval_endpoint],
      ].forEach(([label, value]) => {
        const chip = document.createElement("span");
        chip.className = "pill info";
        chip.textContent = `${label}: ${value || "—"}`;
        els.snapshotChips.appendChild(chip);
      });
      setPill(els.metaStatus, meta.status === "ok" ? "API ready" : "metadata unavailable", meta.status === "ok" ? "ok" : "warn");
    }

    function sampleTicket(overrides = {}) {
      return {
        ticket_id: overrides.ticket_id || "ui_case_001",
        customer_id: overrides.customer_id || "cus_001",
        order_id: overrides.order_id || "ord_001",
        customer_email: overrides.customer_email || "alice@example.com",
        issue_type: overrides.issue_type || "delivered_not_received",
        customer_message:
          overrides.customer_message ||
          "The tracking says delivered, but the package never arrived at my door. Can you help?",
      };
    }

    function formTicketPayload() {
      return {
        ticket_id: document.getElementById("ticketId").value.trim() || "ui_case_001",
        customer_id: document.getElementById("customerId").value.trim() || "cus_001",
        order_id: document.getElementById("orderId").value.trim() || "ord_001",
        customer_email: document.getElementById("customerEmail").value.trim() || "alice@example.com",
        issue_type: document.getElementById("issueType").value,
        customer_message: document.getElementById("customerMessage").value.trim(),
      };
    }

    function currentRunId() {
      const v = document.getElementById("runId").value.trim();
      return v || null;
    }

    function renderQuickFacts(run) {
      const summary = run?.summary || {};
      const qa = run?.qa_result || {};
      const decision = run?.decision || {};
      const items = [
        ["Selected action", decision.selected_action || summary.selected_action || "—"],
        ["QA approved", qa.approved ?? summary.qa_approved ?? "—"],
        ["Escalate to human", qa.escalate_to_human ?? summary.qa_escalate_to_human ?? "—"],
        ["Report path", run?.report_path || summary.report_path || "—"],
      ];
      els.quickFactsList.innerHTML = "";
      for (const [label, value] of items) {
        const li = document.createElement("li");
        li.innerHTML = `<span class=\"label\">${label}</span><span class=\"value\">${String(value)}</span>`;
        els.quickFactsList.appendChild(li);
      }
    }

    function renderRunInsights(run) {
      state.lastRun = run;
      const summary = run.summary || {};
      const decision = run.decision || {};
      const qa = run.qa_result || {};
      const action = run.action_result || {};
      const selectedAction = decision.selected_action || summary.selected_action || "—";
      const checkpoint = summary.status || summary.pipeline_status || summary.current_state || "risk_assessed";
      buildPipeline(checkpoint);
      setPill(els.runStatusPill, run.status || "completed", normalizeStatusKind(run.status || "completed"));
      setPill(els.decisionBadge, selectedAction, normalizeStatusKind(qa.approved ? "approved" : qa.escalate_to_human ? "warn" : "info"));

      els.selectedActionText.textContent = selectedAction === "—"
        ? "No selected action reported."
        : `The pipeline selected ${selectedAction} based on gathered facts, policy constraints, and risk checks.`;
      els.qaOutcomeText.textContent = qa.approved === true
        ? `QA approved the resolution${qa.escalate_to_human ? ", but also requested escalation." : " and found no blocking safety issues."}`
        : qa.escalate_to_human
          ? "QA requested escalation to a human reviewer. Auto execution should not proceed without review."
          : "QA output available in raw JSON details below.";
      els.actionOutcomeText.textContent = action.status
        ? `Action layer result: ${action.status}${action.simulation_mode ? " (simulation mode)" : ""}.`
        : (summary.action_status ? `Summary reports action status: ${summary.action_status}.` : "No action execution result was returned for this run.");
      els.artifactOutcomeText.textContent = run.artifact_dir
        ? `Artifacts generated in ${run.artifact_dir}. Use the artifact inventory below to inspect what was recorded.`
        : "No artifact directory reported.";

      setPre(els.caseRunJson, run);
      setPre(els.caseSummaryJson, summary);
      renderQuickFacts(run);

      if (run.run_id) {
        loadArtifacts(run.run_id).catch((err) => {
          showToast(`Artifact lookup failed: ${err.message}`, "warn");
        });
      }
    }

    async function loadArtifacts(runId) {
      const payload = await api(`/v1/cases/${encodeURIComponent(runId)}/artifacts`);
      state.lastArtifacts = payload;
      setPre(els.artifactJson, payload);
      els.artifactList.innerHTML = "";
      for (const file of (payload.files || [])) {
        const li = document.createElement("li");
        li.innerHTML = `
          <span class="label">${file.name}</span>
          <span class="value">${file.path}</span>
          <span class="tiny">${file.size_bytes} bytes</span>
        `;
        els.artifactList.appendChild(li);
      }
      if (!payload.files || payload.files.length === 0) {
        els.artifactList.innerHTML = '<li><span class="label">No files</span><span class="value">Artifact directory exists but no files were listed.</span></li>';
      }
      return payload;
    }

    function metricToPercentWidth(name, value) {
      if (typeof value !== "number" || Number.isNaN(value)) return 0;
      if (name.includes("rate") || name.includes("accuracy") || name.includes("compliance")) {
        return Math.max(0, Math.min(100, value * 100));
      }
      if (name.includes("turn") || name.includes("tool_calls")) {
        return Math.max(0, Math.min(100, (value / 20) * 100));
      }
      return Math.max(0, Math.min(100, value));
    }

    function renderEval(evalResult) {
      state.lastEval = evalResult;
      setPre(els.evalJson, evalResult);
      setPill(els.evalStatusPill, evalResult.status || "completed", normalizeStatusKind(evalResult.status || "completed"));

      const metrics = evalResult.metrics || {};
      const gate = evalResult.gate || {};
      els.evalScenarioCount.textContent = String(evalResult.scenario_count ?? "—");
      els.evalGateStatus.textContent = gate.passed === true ? "PASS" : gate.passed === false ? "FAIL" : "—";
      els.evalAccuracy.textContent = asPercent(metrics.resolution_accuracy);
      els.evalPolicyCompliance.textContent = asPercent(metrics.policy_compliance_rate);

      els.evalMetricsBoard.innerHTML = "";
      const orderedMetrics = Object.entries(metrics).sort((a, b) => a[0].localeCompare(b[0]));
      for (const [name, value] of orderedMetrics) {
        const row = document.createElement("div");
        row.className = "metric-bar";
        const width = metricToPercentWidth(name, value);
        const displayValue = (name.includes("rate") || name.includes("accuracy") || name.includes("compliance"))
          ? asPercent(value)
          : asNumber(value);
        row.innerHTML = `
          <div class="metric-bar-top">
            <span class="name">${name}</span>
            <span class="val">${displayValue}</span>
          </div>
          <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
        `;
        els.evalMetricsBoard.appendChild(row);
      }

      if (Array.isArray(gate.failures) && gate.failures.length) {
        const failCard = document.createElement("div");
        failCard.className = "metric-bar";
        failCard.innerHTML = `<div class=\"metric-bar-top\"><span class=\"name\">gate_failures</span><span class=\"val\">${gate.failures.length}</span></div><div class=\"footnote\">${gate.failures.join(" | ")}</div>`;
        els.evalMetricsBoard.prepend(failCard);
      }
    }

    async function runCaseWithTicket(ticket, explicitRunId = null) {
      setPill(els.runStatusPill, "running", "warn");
      els.runCustomBtn.disabled = true;
      els.runDemoBtn.disabled = true;
      try {
        const payload = await api("/v1/cases/run", {
          method: "POST",
          body: JSON.stringify({
            ticket,
            simulation: true,
            run_id: explicitRunId,
          }),
        });
        renderRunInsights(payload);
        showToast(`Scenario complete: ${payload.run_id}`, "ok");
        try {
          localStorage.setItem("era:lastTicket", JSON.stringify(ticket));
        } catch (_) {
          // best effort only
        }
        return payload;
      } catch (err) {
        setPill(els.runStatusPill, "error", "bad");
        showToast(`Scenario run failed: ${err.message}`, "bad");
        throw err;
      } finally {
        els.runCustomBtn.disabled = false;
        els.runDemoBtn.disabled = false;
      }
    }

    async function runDemo() {
      const ticket = sampleTicket({
        ticket_id: "ui_delivered_not_received_demo",
        issue_type: "delivered_not_received",
      });
      document.getElementById("ticketId").value = ticket.ticket_id;
      document.getElementById("customerId").value = ticket.customer_id;
      document.getElementById("orderId").value = ticket.order_id;
      document.getElementById("customerEmail").value = ticket.customer_email;
      document.getElementById("issueType").value = ticket.issue_type;
      document.getElementById("customerMessage").value = ticket.customer_message;
      if (!document.getElementById("runId").value.trim()) {
        document.getElementById("runId").value = "ui_demo_delivered_not_received";
      }
      await runCaseWithTicket(ticket, currentRunId());
    }

    async function runMiniEval() {
      setPill(els.evalStatusPill, "running", "warn");
      els.runEvalBtn.disabled = true;
      els.runEvalInlineBtn.disabled = true;
      try {
        const limit = Number(els.evalLimit.value || "8");
        const payload = await api("/v1/evals/run", {
          method: "POST",
          body: JSON.stringify({
            limit,
            write_artifacts: els.evalArtifacts.value === "true",
          }),
        });
        renderEval(payload);
        showToast(`Mini eval complete (${payload.scenario_count} scenarios)`, payload.gate?.passed ? "ok" : "warn");
      } catch (err) {
        setPill(els.evalStatusPill, "error", "bad");
        showToast(`Eval failed: ${err.message}`, "bad");
      } finally {
        els.runEvalBtn.disabled = false;
        els.runEvalInlineBtn.disabled = false;
      }
    }

    function resetForm() {
      const t = sampleTicket();
      document.getElementById("ticketId").value = t.ticket_id;
      document.getElementById("runId").value = "ui_demo_delivered_not_received";
      document.getElementById("customerId").value = t.customer_id;
      document.getElementById("orderId").value = t.order_id;
      document.getElementById("customerEmail").value = t.customer_email;
      document.getElementById("issueType").value = t.issue_type;
      document.getElementById("customerMessage").value = t.customer_message;
      showToast("Sample scenario restored", "ok");
    }

    async function loadBootData() {
      buildPipeline("");
      try {
        const [meta, health] = await Promise.all([
          api("/v1/meta"),
          api("/healthz"),
        ]);
        state.meta = meta;
        state.health = health;
        updateSnapshot();
        setPill(els.runStatusPill, "ready", "ok");
        setPill(els.evalStatusPill, "ready", "ok");
      } catch (err) {
        setPill(els.metaStatus, "metadata unavailable", "bad");
        showToast(`Startup checks failed: ${err.message}`, "bad");
      }

      try {
        const raw = localStorage.getItem("era:lastTicket");
        if (raw) {
          const t = JSON.parse(raw);
          if (t && typeof t === "object") {
            document.getElementById("ticketId").value = t.ticket_id || document.getElementById("ticketId").value;
            document.getElementById("customerId").value = t.customer_id || document.getElementById("customerId").value;
            document.getElementById("orderId").value = t.order_id || document.getElementById("orderId").value;
            document.getElementById("customerEmail").value = t.customer_email || document.getElementById("customerEmail").value;
            if (t.issue_type) document.getElementById("issueType").value = t.issue_type;
            if (t.customer_message) document.getElementById("customerMessage").value = t.customer_message;
          }
        }
      } catch (_) {
        // ignore localStorage parse errors
      }
    }

    function wireEvents() {
      els.runDemoBtn.addEventListener("click", () => { runDemo().catch(() => {}); });
      els.runEvalBtn.addEventListener("click", () => { runMiniEval().catch(() => {}); });
      els.runEvalInlineBtn.addEventListener("click", () => { runMiniEval().catch(() => {}); });
      els.resetFormBtn.addEventListener("click", resetForm);
      els.copyMetaBtn.addEventListener("click", async () => {
        if (!state.meta) {
          showToast("Metadata not loaded yet", "warn");
          return;
        }
        try {
          await navigator.clipboard.writeText(pretty(state.meta));
          showToast("API metadata copied", "ok");
        } catch (_) {
          showToast("Clipboard unavailable in this browser context", "warn");
        }
      });
      els.scenarioForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const ticket = formTicketPayload();
        runCaseWithTicket(ticket, currentRunId()).catch(() => {});
      });
    }

    wireEvents();
    loadBootData();
  </script>
</body>
</html>
"""
