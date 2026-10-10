"""Candidate fixture derived from actual DeepEval sweep case same-name-partial-assignment-3x3.

The selected baseline ordering is one observed PASS permutation from the sweep;
reversing EXPECTED while keeping CALLED fixed is the metamorphic transformation.
"""
EXPECTED = [{'name': 'book', 'input_parameters': {'a': 1, 'b': 2, 'c': 2}}, {'name': 'book', 'input_parameters': {'a': 1, 'b': 1, 'c': 1}}, {'name': 'book', 'input_parameters': {'a': 1, 'b': 1, 'c': 2}}]
CALLED = [{'name': 'book', 'input_parameters': {'a': 1, 'b': 1, 'c': 2}}, {'name': 'book', 'input_parameters': {'a': 1, 'b': 2, 'c': 2}}, {'name': 'book', 'input_parameters': {'a': 1, 'b': 3, 'c': 5}}]
THRESHOLD = 0.60
SHOULD_EXACT_MATCH = False
SHOULD_CONSIDER_ORDERING = False
