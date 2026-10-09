# Stage 1 result — hardening

## Status

**Complete.** Version `0.1.1`.

## What changed

- Canonical workspace containment with `Path.resolve()` + `relative_to()`.
- Symlink rejection while copying task trees.
- Explicit secret-inheritance control is now propagated to evaluator runs.
- POSIX timeouts terminate the full evaluator process group.
- Exact-line evaluator marker protocol with conflicting-marker detection.
- `network: blocked` fails closed because v0.1 has no real network sandbox.
- Native task JSON Schema is enforced at load time and bundled into the package.
- Declared known-invalid candidates remain observable controls rather than being
  treated as baseline failures.
- Known-invalid paths, candidate paths, probe targets, and working directories
  reject absolute paths and `..` traversal.
- Runtime dependency metadata now includes `jsonschema`.
- Repository cleanup ignores generated caches and `egg-info`.

## Verification

Focused hardening suite: **10/10 passed**.

Representative end-to-end checks:

- `healthy-control` → `BOUNDARY_OK`
- `under-constrained-auth` → real `FALSE_ACCEPTANCE` findings
- `over-strict-naming` → real `FALSE_REJECTION` finding
- `broken-environment` → `BASELINE_INVALID`

## Intentionally deferred

- Semantic validation of invariance transformations
- Automatic sensitivity-probe generation beyond current deterministic transforms
- Minimal-counterfactual search
- Real network/container sandbox backend
- Faster corpus execution and parallel scheduling
- Broad benchmark adapters

Those are Stage 2+ problems.
