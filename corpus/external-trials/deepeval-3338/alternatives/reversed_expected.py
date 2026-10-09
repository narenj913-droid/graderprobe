EXPECTED = [
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 1}},
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 2}},
]
CALLED = [
    {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 2}},
    {"name": "book", "input_parameters": {"a": 1, "b": 5, "c": 5}},
]
THRESHOLD = 0.6
