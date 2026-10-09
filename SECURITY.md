# Security

GraderProbe executes evaluator commands and candidate programs. Treat both as
untrusted.

## What is implemented

- Fresh isolated working directories per execution; the source tree is never
  mutated.
- Subprocess boundaries with captured stdout/stderr/exit.
- Timeouts. A timeout is `TIMEOUT`, not `FAIL`.
- POSIX CPU and address-space limits when the platform supports them.
- Secrets whose names contain `TOKEN`, `SECRET`, `PASSWORD`, or `API_KEY` are
  stripped from the child environment by default.
- Writes through the workspace helper refuse paths that escape the temp dir.
- Network defaults to `unrestricted`. A task that requests `network: blocked`
  fails closed in v0.1 because no network sandbox backend is bundled yet; the
  project does not pretend that a subprocess is a network jail.

## What is not implemented

- No container, VM, seccomp, or landlock jail in v0.1.
- No cryptographic signatures (the certificate is a hash manifest).
- No guarantee that a malicious evaluator cannot read the host beyond the
  subprocess user.
- Docker is optional and unused by default.

## Trust model (plain language)

If you point GraderProbe at a third-party benchmark, you are running that
benchmark's evaluator on your machine. Use a dedicated user, a container, or
a throwaway VM when the artifacts are untrusted. GraderProbe reduces accidental
damage; it does not make untrusted code safe.

## Reporting

Open a GitHub issue with `security` in the title. Do not file exploits against
the demo corpus; those evaluators are intentionally defective.


## Contract lock and causal audit

A contract lock protects evaluation configuration and provenance; it is not a security boundary. Frozen-candidate causal attribution copies candidate bytes into isolated Git snapshots but does not provide VM-level isolation. Treat benchmark/evaluator code as untrusted and use the documented Docker backend or an external sandbox for hostile workloads.
