# Candidate input for the upstream DeepEval trial.
# Baseline intentionally uses the order that the public issue reports as PASS.
EXPECTED = [
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 2}},
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 1}},
]
CALLED = [
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 2}},
    {"name": "book", "input_parameters": {"a": 1, "b": 5, "c": 5}},
]
THRESHOLD = 0.6
