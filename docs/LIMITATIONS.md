# Limitations

Passing Boundary Tests does not prove an evaluator is correct.

- **Semantic equivalence is hard.** An "invariance" transform may accidentally
  change behavior. We prefer declared, reviewed alternatives in the demo
  corpus for that reason. AST operators are conservative, not a proof.
- **Model-assisted probes can be wrong.** They are labeled `MODEL_GENERATED`
  and are never ground truth. v0.1's demo does not use them.
- **Insufficient probe diversity misses defects.** A grader can survive every
  probe in a task file and still be wrong on an untested region.
- **Execution environments add artifacts.** Timeouts, locale, floating point,
  and filesystem layout can change verdicts independently of the candidate.
- **Natural-language specifications stay ambiguous.** When we cannot tell, we
  use `INCONCLUSIVE` rather than invent a binary grade.
- **Isolation is not a VM.** See SECURITY.md.
- **n=16 is a demonstration, not a scientific validation of any public
  benchmark.** Do not cite the demo as evidence that SWE-bench (or any other
  suite) is valid or invalid.
- **Absence of a discovered defect is not proof of correctness.**
