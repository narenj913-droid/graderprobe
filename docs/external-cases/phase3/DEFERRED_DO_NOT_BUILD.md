# Deferred until maintainer feedback

Do not add an upstream-specific SDK, dependency, or permanent DeepEval/Inspect AI integration yet.

Reason: both target repositories are moving quickly, and a permanent adapter built before maintainer feedback risks coupling GraderProbe to internal APIs or solving the wrong workflow problem. The current trial bundle intentionally uses each project's public reproduction surface and existing package interfaces.

The next implementation should be driven by what a maintainer actually asks for after a trial: e.g. a regression-test helper, changed-file integration, SARIF wiring, or a repository-native action example.
