# Agent notes

This repository is evaluation infrastructure, not an application to "productize"
into a chatbot or leaderboard.

## Do

- Keep the deterministic core offline.
- Preserve `PASS`/`FAIL`/`ERROR`/`TIMEOUT`/`INCONCLUSIVE` as distinct states.
- Refuse to emit a boundary score when baseline validation fails.
- Put evidence on every finding.
- Keep a fast deterministic PR suite separate from subprocess-heavy integration tests.
- Run the fast suite on every change; run the heavy suite with an explicit time budget before releases.
- The demo must remain offline and must not call a model provider.

## Do not

- Call a model provider from the demo.
- Hard-code findings. They must come from executing defective evaluators.
- Claim the project is affiliated with OpenAI or required by anyone.
- Invent users, stars, or benchmark validity from n=16.
