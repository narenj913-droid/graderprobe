"""Self-contained HTML profile. No external assets."""

from __future__ import annotations

import html

from graderprobe.profile import BoundaryIntegrityProfile


def render_html(profile: BoundaryIntegrityProfile) -> str:
    m = profile.metrics
    rows = []
    for pair in profile.pairs:
        rows.append(
            "<tr>"
            f"<td>{_e(pair.pair_id)}</td>"
            f"<td>{_e(pair.probe.id)}</td>"
            f"<td>{_e(pair.probe.probe_class.value)}</td>"
            f"<td>{_e(pair.baseline_verdict.value)} → {_e(pair.actual_verdict.value)}</td>"
            f"<td>{_e(pair.finding.type.value)}</td>"
            f"<td>{_e(pair.transformation_description)}</td>"
            "</tr>"
        )
    table = "\n".join(rows) or "<tr><td colspan='6'>No pairs (baseline invalid or empty).</td></tr>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>GraderProbe — {html.escape(profile.task_id)}</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ font: 15px/1.45 ui-sans-serif, system-ui, sans-serif; background:#0b0c0e; color:#e8e6e1; margin:0; }}
  main {{ max-width: 980px; margin: 0 auto; padding: 32px 20px 64px; }}
  h1 {{ font-weight: 560; letter-spacing: -0.03em; font-size: 28px; }}
  .muted {{ color:#8b8a86; }}
  .card {{ border:1px solid #2a2b2e; border-radius:16px; padding:20px; margin:16px 0; background:#141518; }}
  table {{ width:100%; border-collapse: collapse; font-size:13px; }}
  th, td {{ text-align:left; padding:8px 6px; border-bottom:1px solid #2a2b2e; vertical-align:top; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .v {{ font-variant-numeric: tabular-nums; }}
</style>
</head>
<body>
<main>
  <p class="muted">GraderProbe boundary integrity profile</p>
  <h1>{html.escape(profile.task_id)}</h1>
  <p>{html.escape(profile.task_title)}</p>
  <div class="card">
    <p>Baseline: <code>{html.escape(profile.baseline.verdict.value)}</code></p>
    <p>Profile verdict: <code>{html.escape(profile.verdict.value)}</code></p>
    <p class="v">Invariance {m.invariance_preserved}/{m.invariance_executed}
       · Sensitivity {m.sensitivity_detected}/{m.sensitivity_executed}
       · FA {m.false_acceptance_count} · FR {m.false_rejection_count}</p>
  </div>
  <div class="card">
    <table>
      <thead><tr><th>Pair</th><th>Probe</th><th>Class</th><th>Verdicts</th><th>Finding</th><th>Transformation</th></tr></thead>
      <tbody>
      {table}
      </tbody>
    </table>
  </div>
  <p class="muted">Passing Boundary Tests does not prove an evaluator is correct.</p>
</main>
</body>
</html>
"""


def _e(value: str) -> str:
    return html.escape(str(value))
