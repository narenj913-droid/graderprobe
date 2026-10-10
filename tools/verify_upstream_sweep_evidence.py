#!/usr/bin/env python3
"""Verify the copied actual-DeepEval sweep evidence without importing DeepEval."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check_side(name, expected_failures):
    p=ROOT/'evidence'/'results'/({'base_sweep.json':'base/base-sweep.json','pr_head_sweep.json':'pr_head/pr-sweep.json'}[name])
    d=json.loads(p.read_text(encoding='utf-8'))
    assert d['case_count']==126, (name,d['case_count'])
    assert d['total_measurements']==1695, (name,d['total_measurements'])
    assert len(d['unexpected_exceptions'])==0
    fails=d['unordered_invariance_failures']
    assert len(fails)==expected_failures, (name,len(fails))
    return d
base=check_side('base_sweep.json',10)
pr=check_side('pr_head_sweep.json',0)
base_by={c['case_id']:c for c in base['case_reports']}
flips=[]
score_only=[]
for c in base['unordered_invariance_failures']:
    row=base_by[c['case_id']]
    if len(row['verdicts'])>1: flips.append(row['case_id'])
    else: score_only.append(row['case_id'])
assert len(flips)==3, flips
assert len(score_only)==7, score_only
assert pr['order_sensitive_control']['passed'] is True
assert pr['exact_match_exploratory'], 'missing exploratory exact-match lane'
manifest=ROOT/'evidence/results/SHA256SUMS.txt'
for line in manifest.read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    expected, rel=line.split('  ',1)
    fp=ROOT/'evidence/results'/rel
    if not fp.is_file():
        raise SystemExit(f'MISSING {rel}')
    actual=hashlib.sha256(fp.read_bytes()).hexdigest()
    if actual != expected: raise SystemExit(f'HASH MISMATCH {rel}: {actual} != {expected}')
print('PASS: base=10 order-invariance failures; PR head=0; exceptions=0; order-sensitive control passes.')
print('PASS: exactly 3/10 cases flip threshold verdict; 7/10 only show score drift without verdict flip at threshold=0.60.')
print('PASS: upstream evidence manifest hashes verified.')
print('IMPORTANT: this verifies sweep artifacts only. It does NOT claim GraderProbe detected any case until the runbook is executed.')
