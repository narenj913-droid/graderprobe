# Same expected_tools multiset, reversed. The public issue reports this changes
# the documented unordered-mode score from 0.6667 to 0.5.
EXPECTED = [
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 1}},
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 2}},
]
CALLED = [
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 2}},
    {"name": "book", "input_parameters": {"a": 1, "b": 5, "c": 5}},
]
THRESHOLD = 0.6
