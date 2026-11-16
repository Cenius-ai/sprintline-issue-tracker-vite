"""Server-rendered landing page for the API origin.

The product UI is the Vite React app; this page exists so ``GET /`` on the API
origin is a real human surface (status, demo credential, endpoint index) rather
than a JSON blob. No inline scripts — the CSP only allows same-origin scripts.

The UI origin is read from ``FRONTEND_URL`` so the page points at the right host
behind a proxy or on a real domain; it defaults to the local dev server.
"""

from __future__ import annotations

import os
from html import escape

DEFAULT_FRONTEND_URL = "http://localhost:5173"

_STYLE = """
:root {
  --background: #0c0c11; --foreground: #efeff5; --card: #16161d;
  --muted: #212127; --muted-foreground: #9d9da6; --border: #2d2d34;
  --accent: #9884f3; --on-accent: #111111;
  --font: 'Atkinson Hyperlegible', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--background); color: var(--foreground);
  font-family: var(--font); font-size: 16px; line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
main { width: min(100% - 2rem, 56rem); margin: 0 auto; padding: 48px 0 64px; }
.mark { display: flex; align-items: center; gap: 10px; font-weight: 700; letter-spacing: 0.02em; }
.mark span.glyph { color: var(--accent); }
h1 { font-size: clamp(1.9rem, 4vw, 2.5rem); line-height: 1.15; margin: 24px 0 8px; }
p.lead { color: var(--muted-foreground); margin: 0 0 32px; max-width: 46ch; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr)); gap: 12px; margin-bottom: 32px; }
.tile {
  background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px;
}
.tile .value { font-size: 1.75rem; font-weight: 700; font-variant-numeric: tabular-nums; }
.tile .label { color: var(--muted-foreground); font-size: 0.8125rem; }
.card {
  background: var(--card); border: 1px solid var(--border); border-radius: 10px;
  padding: 20px 24px; margin-bottom: 16px;
}
.card h2 { font-size: 0.9375rem; text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 12px; color: var(--muted-foreground); }
ul { list-style: none; margin: 0; padding: 0; }
li { padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 0.9375rem; }
li:last-child { border-bottom: 0; }
li::before { content: "\\25C6"; color: var(--accent); margin-right: 10px; font-size: 0.75rem; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.875rem; background: var(--muted); padding: 2px 6px; border-radius: 4px; }
a { color: var(--accent); }
.credential { display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: 0.9375rem; }
.credential strong { font-variant-numeric: tabular-nums; }
footer { color: var(--muted-foreground); font-size: 0.8125rem; margin-top: 32px; }
"""


def frontend_origin() -> str:
    """Public URL of the UI. Overridable for split/off-localhost deploys."""
    raw = (os.environ.get("FRONTEND_URL") or "").strip() or DEFAULT_FRONTEND_URL
    return raw.rstrip("/")


def render_landing(counts: dict[str, int]) -> str:
    """Render the API origin landing page with live counts."""
    ui_origin = frontend_origin()
    ui_label = ui_origin.split("://", 1)[-1]
    tiles = [
        ("Issues", counts.get("issues", 0)),
        ("Sprints", counts.get("sprints", 0)),
        ("Projects", counts.get("projects", 0)),
        ("Teammates", counts.get("users", 0)),
    ]
    tile_html = "".join(
        f'<div class="tile"><div class="value">{int(value)}</div>'
        f'<div class="label">{escape(str(label))}</div></div>'
        for label, value in tiles
    )
    endpoints = [
        ("POST", "/api/auth/login", "Email + password → JWT session token"),
        ("GET", "/api/auth/me", "Current user profile"),
        ("GET", "/api/issues", "Filtered issue list (status, priority, assignee, label, sprint, project, q)"),
        ("POST", "/api/issues", "Create an issue and record a created event"),
        ("GET", "/api/issues/{id}", "Issue detail with project, sprint, assignee and labels"),
        ("PATCH", "/api/issues/{id}", "Partial update with activity events"),
        ("DELETE", "/api/issues/{id}", "Delete an issue with its comments and activity"),
        ("GET", "/api/issues/{id}/comments", "Comment stream, oldest first"),
        ("POST", "/api/issues/{id}/comments", "Add a comment"),
        ("GET", "/api/issues/{id}/activity", "Append-only activity history"),
        ("GET", "/api/sprints/{id}/burndown", "Ideal vs actual remaining points"),
        ("GET", "/api/roadmap", "Now / Next / Later / Done lanes per project"),
    ]
    endpoint_html = "".join(
        f"<li><code>{escape(method)} {escape(path)}</code> — {escape(description)}</li>"
        for method, path, description in endpoints
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Sprintline API</title>
<style>{_STYLE}</style>
</head>
<body>
<main>
  <div class="mark"><span class="glyph">&#9670;</span> Sprintline</div>
  <h1>Issue tracking for small engineering teams</h1>
  <p class="lead">This is the Sprintline API origin. The product UI is the Vite React app — start it with
  <code>npm run dev</code> in <code>frontend/</code> and open
  <a href="{escape(ui_origin)}">{escape(ui_label)}</a>; the dev server proxies <code>/api</code> here.
  Set <code>FRONTEND_URL</code> to point this link at a different host.</p>

  <div class="tiles">{tile_html}</div>

  <section class="card">
    <h2>Demo account</h2>
    <div class="credential">
      <span>Email <strong>cenius@cenius.ai</strong></span>
      <span>Password <strong>cenius</strong></span>
    </div>
  </section>

  <section class="card">
    <h2>Endpoints</h2>
    <ul>{endpoint_html}</ul>
  </section>

  <section class="card">
    <h2>Developer docs</h2>
    <ul>
      <li><a href="/docs">Interactive OpenAPI docs (/docs)</a></li>
      <li><a href="/api/health">Health probe (/api/health)</a></li>
    </ul>
  </section>

  <footer>Sprintline Issue Tracker · FastAPI + SQLite + React · MIT licensed</footer>
</main>
</body>
</html>"""
