"""Counterfactual: reverse expected tool order; keep called trajectory unchanged."""
EXPECTED = [{'name': 'book', 'input_parameters': {'a': 1, 'b': 1, 'c': 1}}, {'name': 'book', 'input_parameters': {'a': 1, 'b': 1, 'c': 2}}]
CALLED = [{'name': 'book', 'input_parameters': {'a': 1, 'b': 1, 'c': 2}}, {'name': 'book', 'input_parameters': {'a': 1, 'b': 5, 'c': 5}}]
THRESHOLD = 0.60
SHOULD_EXACT_MATCH = False
SHOULD_CONSIDER_ORDERING = False
