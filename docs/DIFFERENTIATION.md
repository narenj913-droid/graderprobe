# Differentiation

The contribution is: **probe the evaluator's decision boundary with paired
counterfactuals.**

The system is built to answer:

1. What changes leave correctness unchanged?
2. What minimal changes should invalidate correctness?
3. Does the evaluator respond correctly to both?
4. Can the evaluator distinguish semantic correctness from implementation identity?
5. Are there regions where the evaluator is too permissive?
6. Are there regions where the evaluator is too strict?

## Against muteval

muteval asks: if I degrade the *system under test*, do my evals fail?
That is one-sided mutation testing of evals. It is useful. It does not
construct a still-correct alternative and demand that the eval still pass.

## Against BenchJack / reward-hack scanners

Those tools hunt *false acceptance* via exploits (leaked answers, hijacked
scorers). They rarely hunt *false rejection* of a valid rewrite. Over-strict
hidden tests are a documented failure mode in SWE-bench Verified and SWE-bench
Pro audits; GraderProbe treats that mode as a first-class probe class.

## Against generic runners

A runner tells you the gold patch passed. GraderProbe tells you what happened
when the gold patch was rewritten without changing behavior, and when one
required behavior was removed.

## Against a single score

We refuse a default "benchmark quality = 87/100." Optional boundary stability
is labeled as the unweighted mean of two rates on the probes that actually
ran. n is reported. For n<30 we do not print confidence intervals.
