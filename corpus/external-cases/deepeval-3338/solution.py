# Same expected_tools multiset as the public issue #3338 repro.
# Baseline order deliberately puts the stronger exact match first.
EXPECTED = [
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 2}},
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 1}},
]
CALLED = [
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 2}},
    {"name": "book", "input_parameters": {"a": 1, "b": 5, "c": 5}},
]
THRESHOLD = 0.6
