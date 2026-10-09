# Examples

The primary worked examples are the offline corpus:

```text
corpus/tasks/healthy-control/task.yaml
corpus/tasks/under-constrained-auth/task.yaml
```

Run one task:

```bash
graderprobe run corpus/tasks/healthy-control/task.yaml --out /tmp/gp --fail-on none
```

A SWE-bench-style stub (not a SWE-bench run) lives in `swebench_stub.yaml`.
