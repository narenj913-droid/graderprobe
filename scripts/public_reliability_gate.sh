#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m graderprobe --version
python -m graderprobe --help >/dev/null

modules=(
  tests.test_findings
  tests.test_transforms
  tests.test_task_schema
  tests.test_stage1_hardening
  tests.test_stage3_ast
  tests.test_stage8_causal_lock
)

for module in "${modules[@]}"; do
  python -m unittest -q "$module"
done

# Reuse the same subprocess-bounded smoke test as the unit suite. This avoids
# maintaining two slightly different CLI smoke implementations in the gate.
python -m unittest -q tests.test_public_reliability

# Contract-lock workflow must fail clearly rather than silently skip missing lockfiles.
grep -Fq "Require committed evaluation contract lock" .github/workflows/contract-lock.yml
grep -Fq "if [ ! -f graderprobe.lock.json ]" .github/workflows/contract-lock.yml
grep -Fq "graderprobe.lock.json is required" .github/workflows/contract-lock.yml
grep -Fq "hashFiles('graderprobe.lock.json') != ''" .github/workflows/contract-lock.yml && {
  echo "Contract-lock workflow must not silently skip when the lockfile is missing." >&2
  exit 1
}

printf '%s\n' 'public reliability gate: PASS'
