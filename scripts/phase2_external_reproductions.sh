#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

run_expected_failure() {
  local task="$1"
  local out="$2"
  set +e
  python -m graderprobe run "$task" --out "$out" --workers 1 --execution-slots 1 --fail-on high
  local rc=$?
  set -e
  if [[ "$rc" -ne 3 ]]; then
    echo "unexpected GraderProbe exit code for $task: $rc" >&2
    exit 1
  fi
}

run_expected_failure corpus/external-cases/deepeval-3338/task.yaml /tmp/deepeval-3338-profile
run_expected_failure corpus/external-cases/inspect-ai-4721/task.yaml /tmp/inspect-ai-4721-profile

printf '%s\n' 'phase 2 external reproductions: PASS (both expected BOUNDARY_FAIL findings reproduced)'
