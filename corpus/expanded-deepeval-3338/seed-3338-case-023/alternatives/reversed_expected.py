"""Counterfactual: reverse expected tool order; keep called trajectory unchanged."""
EXPECTED = [{'name': 'refund', 'input_parameters': {'a': 1, 'status': 1}}, {'name': 'book', 'input_parameters': {'c': 0, 'b': 0}}, {'name': 'refund', 'input_parameters': {'a': 0}}, {'name': 'refund', 'input_parameters': {'a': 1, 'b': 'ok', 'status': 'ok'}}]
CALLED = [{'name': 'book', 'input_parameters': {'c': 0, 'b': 0}}, {'name': 'refund', 'input_parameters': {'a': 0}}, {'name': 'refund', 'input_parameters': {'a': 1, 'b': 'ok', 'status': 'pending'}}]
THRESHOLD = 0.60
SHOULD_EXACT_MATCH = False
SHOULD_CONSIDER_ORDERING = False
