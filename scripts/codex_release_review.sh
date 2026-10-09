#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"
OUT="${2:-graderprobe-out/codex-release-review.json}"
MODEL="${GRADERPROBE_CODEX_MODEL:-}"
MODEL_ARGS=()
if [ -n "$MODEL" ]; then MODEL_ARGS=(--model "$MODEL"); fi

mkdir -p "$(dirname "$OUT")"
SCHEMA="$(mktemp)"
trap 'rm -f "$SCHEMA"' EXIT

cat > "$SCHEMA" <<'JSON'
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "risk": {"type": "string", "enum": ["low", "medium", "high"]},
    "recommendation": {"type": "string", "enum": ["allow", "review", "block"]},
    "checks": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
    "rationale": {"type": "string"}
  },
  "required": ["risk", "recommendation", "checks", "rationale"]
}
JSON

cat <<'PROMPT' | codex exec \
  "${MODEL_ARGS[@]}" \
  --sandbox read-only \
  --ask-for-approval never \
  --output-schema "$SCHEMA" \
  --output-last-message "$OUT" \
  -
Review the current Git repository's GraderProbe release-assurance artifacts as a maintainer.
Do not modify files.
Inspect the current release-assurance JSON/Markdown output if present and the repository diff against its base revision.
Return a conservative structured assessment. Do not decide benchmark correctness; identify release risk and the smallest additional checks worth running.
PROMPT

echo "$OUT"
