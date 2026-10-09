#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASK="${1:?task path required}"
OUT="${2:?output directory required}"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

set +e
python -m graderprobe run "$TASK" --out "$OUT" --workers 1 --execution-slots 1 --fail-on high
rc=$?
set -e

if [[ "$rc" -ne 3 ]]; then
  echo "unexpected GraderProbe exit code: $rc" >&2
  exit "$rc"
fi

echo "GRADERPROBE_BOUNDARY_FAIL_EXPECTED=3"
echo "evidence=$OUT/profile.json"
