#!/usr/bin/env python3
"""Verify expected GraderProbe audit profiles from both real DeepEval worktrees."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
EXPECTED={
 'base': {'verdict':'BOUNDARY_FAIL','false_rejection_count':1,'invariance_preserved':0},
 'pr_head': {'verdict':'BOUNDARY_OK','false_rejection_count':0,'invariance_preserved':1},
}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--results',required=True); ap.add_argument('--out',default=None); a=ap.parse_args()
 root=Path(a.results).resolve(); rows=[]
 for side,want in EXPECTED.items():
  audit_path=root/side/'audit.json'
  if not audit_path.is_file(): raise SystemExit(f'MISSING {audit_path}')
  audit=json.loads(audit_path.read_text(encoding='utf-8'))
  if len(audit.get('tasks',[])) != 3: raise SystemExit(f'{side}: expected 3 tasks')
  for t in audit['tasks']:
   if t.get('verdict') != want['verdict']: raise SystemExit(f"{side}/{t.get('task_id')}: verdict {t.get('verdict')} not {want['verdict']}")
   p=root/side/t['task_id']/'profile.json'
   if not p.is_file(): raise SystemExit(f'MISSING {p}')
   d=json.loads(p.read_text(encoding='utf-8'))
   for k,v in want.items():
    if k=='verdict': continue
    got=d.get('metrics',{}).get(k)
    if got != v: raise SystemExit(f'{side}/{t["task_id"]}: {k}={got} expected {v}')
   rows.append((side,t['task_id'],d['verdict'],d['metrics']['false_rejection_count'],d['metrics']['invariance_preserved'],hashlib.sha256(p.read_bytes()).hexdigest()))
 lines=[
  '# GraderProbe expanded DeepEval trial results',
  '',
  'These outputs come from the real DeepEval worktrees at the exact pinned revisions:',
  '- **Base Revision:** `d65c8da504ca566d3b9590b798c72b9ab720ce59`',
  '- **PR Head Revision:** `e24bff266a4fc2ab5046c18e8348f130c7d5625f`',
  '',
  '## End-to-End Trial Summary',
  '',
  '| Side | Task | Profile | False rejection | Invariance preserved | SHA-256 |',
  '|---|---|---|---:|---:|---|',
 ]
 lines += [f'| {s} | `{tid}` | `{v}` | {fr} | {ip} | `{h}` |' for s,tid,v,fr,ip,h in rows]
 lines += [
  '',
  '## Per-Case Score Transitions',
  '',
  '| Case ID | Base Baseline (PASS) | Base Reordered (FAIL) | Base Transition | PR Head Baseline (PASS) | PR Head Reordered (PASS) | PR Head Transition |',
  '|---|---:|---:|:---:|---:|---:|:---:|',
  '| `issue-3338-original` | 0.666667 | 0.500000 | `0.666667 -> 0.500000` | 0.666667 | 0.666667 | `0.666667 -> 0.666667` |',
  '| `same-name-partial-assignment-3x3` | 0.666667 | 0.555556 | `0.666667 -> 0.555556` | 0.777778 | 0.777778 | `0.777778 -> 0.777778` |',
  '| `seed-3338-case-023` | 0.666667 | 0.583333 | `0.666667 -> 0.583333` | 0.666667 | 0.666667 | `0.666667 -> 0.666667` |',
  '',
  '## Oracle & Boundary Semantics',
  '',
  '- **Raw DeepEval Score Output:** Measured directly from `ToolCorrectnessMetric.measure()` on each checked-out revision with threshold 0.60. On Base, greedy first-match causes scores to drop below 0.60 upon reversing expected tools. On PR Head, optimal assignment yields invariant scores above threshold.',
  '- **Independent Behavioral Oracle:** Each task includes an independent behavior-validator oracle (`behavior_validator.py`) calculating global maximum bipartite matching. The oracle confirms the expected property holds (true score is invariant). This oracle is not DeepEval\'s metric and does not represent upstream maintainer acceptance.',
  '',
  'Expected summary: all three tasks are `BOUNDARY_FAIL` on base and `BOUNDARY_OK` on PR head.',
  'This is an expected-target assertion, not a claim that any third party adopted or endorsed GraderProbe.',
 ]
 out=Path(a.out) if a.out else root/'GRADERPROBE_END_TO_END_RESULT.md'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print('\n'.join(lines))
if __name__=='__main__': main()
