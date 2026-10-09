# Contributing

Thank you for considering a contribution. GraderProbe is local-first evaluation
infrastructure. Please keep it that way.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e . -r requirements-dev.txt
python -m unittest discover -s tests
python -m graderprobe demo --out /tmp/gp-demo
```

## Rules

- Do not add a required cloud API.
- Do not collapse the profile into a single proprietary score.
- Do not convert `ERROR`/`TIMEOUT` into `FAIL`.
- Do not mutate the caller's tree; use isolated workspaces.
- Every finding needs pair evidence.
- New transforms need a unit test and a description of the intended relation.
- New corpus tasks must be original, license-clean, and runnable offline.
- Do not fabricate adoption, stars, or research results.

## Pull requests

- Small, reviewable diffs.
- Tests for the behavior you changed.
- Docs only when the contract changed.
