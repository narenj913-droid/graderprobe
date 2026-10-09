# Phase 4 — Selection evidence review

Snapshot: 2026-10-06

This document separates externally verified facts from inference. It is intentionally conservative.

## A. Current official application surface

The current OpenAI Codex for Open Source form asks for maintainer identity, GitHub repository, maintainer role, a 500-character explanation of why the repository qualifies, whether Codex Security/API credits are requested, a 500-character API-credit use case, and optional additional context. It says applications are reviewed on a rolling basis. Source: https://openai.com/form/codex-for-oss/

The public program page says OpenAI looks for active open-source projects with meaningful usage, broad adoption, or clear ecosystem importance, and reviews signals such as repository usage, ecosystem importance, and active maintenance. It also explicitly mentions PR review, issue triage, and release management. Source: https://openai.com/form/codex-for-oss/

## B. Publicly reported selections / accepted recipients

### Discourse

Sam Saffron, a core Discourse maintainer, publicly stated on the OpenAI developer community that several people from Discourse were accepted. In the same thread he described using Codex for a long security-review loop over the Discourse repository.

Source: https://community.openai.com/t/codex-for-open-source-2026/1376418

Interpretation: strong evidence for established project + real maintainer workload + concrete Codex fit. It is not evidence of a numerical threshold.

### Cherry Studio

A core developer/maintainer of Cherry Studio publicly stated that he was accepted into Codex for Open Source and received six months of ChatGPT Pro. The repository currently shows a large active project footprint.

Source: https://community.openai.com/t/codex-for-open-source-2026/1376418
Repository: https://github.com/CherryHQ/cherry-studio

Interpretation: strong evidence for active, high-visibility project; still no proof that stars alone caused selection.

### Super Productivity

The maintainer of Super Productivity publicly documented being accepted into Codex for Open Source on 2026-08-07 in an issue on the public OpenAI Codex repository. The issue identifies the project at roughly 21k stars at the time of the report.

Source: https://github.com/openai/codex/issues/42620

Interpretation: clear accepted-recipient evidence tied to an established, large project. The issue is about benefit activation, not selection criteria.

### mycli / CodeRunner

A public Hacker News thread contains maintainer comments reporting that mycli and CodeRunner received the program benefit. These are self-reported recipient statements rather than official selection lists.

Source: https://news.ycombinator.com/item?id=48497195

Interpretation: useful counter-evidence against a hard minimum-star theory because these reports include projects with very different sizes.

## C. Publicly reported non-selection / no-response cases

These are not official rejection records. They are maintainer reports of applying and not hearing back.

### Filestash

A maintainer reported in the same Hacker News discussion that Filestash had more than 14k GitHub stars and millions of users yet had not heard back after applying.

Source: https://news.ycombinator.com/item?id=48497195

### EasyInvoicePDF

A maintainer reported two applications without a response, while describing roughly 900+ stars, 2k monthly users, and 10k total invoices downloaded.

Source: https://news.ycombinator.com/item?id=48497195

### Other large-project reports

The same public discussion contains reports of roughly 13k–15k stars and very large download counts without a response. These are anonymous/self-reported and must not be treated as named official rejections.

Source: https://news.ycombinator.com/item?id=48497195

## D. What the evidence supports

1. There is no publicly verified hard star threshold.
2. Large popularity does not guarantee a response.
3. Selection recipients include both established, highly visible projects and at least some smaller or newer projects.
4. Active maintainer work is a recurring theme among selected projects.
5. A concrete maintenance workload that Codex can materially reduce is a stronger story than a generic statement that Codex will help write code.
6. For an early project, ecosystem importance and a distinctive technical problem can plausibly compensate for weaker popularity, but this is an inference and not a published rule.

## E. GraderProbe-specific gap assessment

### Strong, directly verified in the repository

- Offline deterministic core.
- Contract-lock and release-assurance machinery.
- Causal attribution artifacts.
- SARIF / GitHub Actions integration.
- Reproducibility-oriented evidence output.
- Public-source reproductions for DeepEval #3338, DeepEval #3025, and historical Inspect AI #4721.
- Dedicated trial runners that preserve upstream git HEAD when an authorized maintainer executes them.

### Strong public ecosystem relevance, but not yet adoption proof

GraderProbe targets evaluation quality assurance: detecting cases where an evaluator changes its verdict because of irrelevant perturbations such as order or scheduling. OpenAI's own public eval documentation discusses model-graded evaluation and recommends meta-evals to ensure grader quality, which is conceptually aligned with GraderProbe's thesis.

Source: https://github.com/openai/evals/blob/main/docs/build-eval.md
Source: https://github.com/openai/evals/blob/main/docs/eval-templates.md

### Current weak signals

- No independent maintainer-owned workflow run has been captured yet.
- No external repository has publicly retained GraderProbe in CI yet.
- No upstream maintainer endorsement has been captured.
- Project age and public usage history are still short.

## F. Decision rule

Do not submit an application solely because the code is good.

Do not delay indefinitely waiting for an arbitrary star count.

The highest-value next evidence is one authorized upstream execution on DeepEval #3338, followed by one external maintainer-owned workflow or a small upstream contribution accepted by a maintainer.

The 30% figure is an internal target, not a statistical claim about OpenAI selection probability.
