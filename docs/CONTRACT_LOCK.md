# Evaluation-contract lock

`graderprobe.lock.json` is a source-controlled snapshot of the evaluation surface at an approved Git revision.

It records:

- approved commit
- task inventory and task-tree digests
- evaluator contract information
- probe-set digests
- optional behavioral anchor fingerprints
- a lock fingerprint covering the complete manifest

Create it from a clean working tree:

```bash
graderprobe lock . --task-root corpus/tasks --out graderprobe.lock.json --anchors 2
```

Verify it:

```bash
graderprobe verify-lock . --lock graderprobe.lock.json
```

Verification is intentionally conservative. A documentation-only change can pass without execution. A change to the evaluation surface is escalated to release assurance. The lock can be regenerated after a maintainer has reviewed and approved the new evaluation behavior.

The lock is not cryptographic attestation of correctness; it is a reproducible change-control artifact.
