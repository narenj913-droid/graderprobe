# Maintainer Runbook — external validation

The goal of this runbook is a real upstream execution by a repository owner/authorized developer. It does not modify the upstream checkout.

## DeepEval #3338

From a clean GraderProbe checkout:

```bash
python scripts/external_trials/deepeval_3338_upstream.py \
  --upstream-repo /path/to/deepeval \
  --require-issue-revision \
  --out /tmp/deepeval-3338-upstream.json
```

Then run GraderProbe against the recorded case:

```bash
PYTHONPATH=/path/to/deepeval/src:/path/to/deepeval:$PYTHONPATH \
python -m graderprobe run \
  corpus/external-trials/deepeval-3338/task.yaml \
  --out /tmp/graderprobe-deepeval-3338 \
  --workers 1 --execution-slots 1 --fail-on high
```

The JSON and profile are the evidence objects. Preserve the upstream `git rev-parse HEAD` value and do not rewrite the result after execution.

## DeepEval #3025

The same pattern applies to the sync/async trial:

```bash
python scripts/external_trials/deepeval_3025_upstream.py \
  --repo /path/to/deepeval \
  --require-issue-revision \
  --out /tmp/deepeval-3025-upstream.json
```

For the declaration-order companion, use:

```bash
python scripts/external_trials/deepeval_3025_declaration_order_upstream.py \
  --upstream-repo /path/to/deepeval \
  --require-issue-revision \
  --out /tmp/deepeval-3025-order.json
```

## Inspect AI #4721

This issue has since been fixed/closed through external PR #4769. A fresh run should therefore be treated as a historical reproduction check unless the maintainer chooses a revision before the fix.

```bash
python scripts/external_trials/inspect_ai_4721_upstream.py \
  --upstream-repo /path/to/inspect_ai \
  --require-issue-revision \
  --out /tmp/inspect-ai-4721-upstream.json
```

The historical issue and merged PR are retained as proof that an external contribution path is real, not as evidence that the bug still exists on today's main.
