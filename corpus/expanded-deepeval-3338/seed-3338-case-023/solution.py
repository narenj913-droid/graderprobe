"""Candidate fixture derived from actual DeepEval sweep case seed-3338-case-023.

The selected baseline ordering is one observed PASS permutation from the sweep;
reversing EXPECTED while keeping CALLED fixed is the metamorphic transformation.
"""
EXPECTED = [{'name': 'refund', 'input_parameters': {'a': 1, 'b': 'ok', 'status': 'ok'}}, {'name': 'refund', 'input_parameters': {'a': 0}}, {'name': 'book', 'input_parameters': {'c': 0, 'b': 0}}, {'name': 'refund', 'input_parameters': {'a': 1, 'status': 1}}]
CALLED = [{'name': 'book', 'input_parameters': {'c': 0, 'b': 0}}, {'name': 'refund', 'input_parameters': {'a': 0}}, {'name': 'refund', 'input_parameters': {'a': 1, 'b': 'ok', 'status': 'pending'}}]
THRESHOLD = 0.60
SHOULD_EXACT_MATCH = False
SHOULD_CONSIDER_ORDERING = False
