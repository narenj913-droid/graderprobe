# Codex CLI maintainer workflow

GraderProbe can be used as the deterministic release-assurance layer underneath a Codex-driven maintainer review. The helper script `scripts/codex_release_review.sh` asks Codex for a conservative, structured review of the already-generated release-assurance evidence; it does not permit Codex to modify files and does not make the model the release oracle.

The script follows the current Codex CLI pattern of non-interactive `codex exec`, read-only sandboxing, no approval prompts, an explicit output schema, and a saved last-message artifact. A maintainer must have a working Codex CLI installation and the appropriate account access.

Recommended order:

```text
GraderProbe deterministic release-audit
        ↓
JSON/Markdown/SARIF evidence
        ↓
optional Codex CLI maintainer review
        ↓
human maintainer decision
```

The deterministic report remains authoritative for GraderProbe's gate. The Codex output is advisory context only.
