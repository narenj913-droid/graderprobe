# Reproducibility

## Demo

```bash
pip install -e .
python -m graderprobe demo --out /tmp/gp-demo
```

- No API keys.
- The demo uses the default `network: unrestricted`; a request for `network: blocked` is refused until a real sandbox backend is available.
- `PYTHONHASHSEED=0` in child processes.
- Transforms are deterministic.
- The non-determinism *task* is detected by repeating the baseline with
  `GRADERPROBE_ATTEMPT` set to 1 and 2. The defective evaluator keys off that
  harness field so the qualitative finding (`BASELINE_INVALID`) is stable.

## What should match across machines

Qualitative findings: which tasks are `BOUNDARY_FAIL`, `BOUNDARY_OK`,
`BASELINE_INVALID`, or `INCONCLUSIVE`, and which probe ids produce false
acceptance/rejection. Wall-clock `duration_ms` will not match. Temp paths
will not match. Certificate hashes of the task tree should match for the
same revision.

## Seeds

`--` the runner records `seed: 0` in the environment manifest. v0.1 has no
randomized probe generation in the demo path.
