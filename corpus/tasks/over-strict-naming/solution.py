def sum_evens(values):
    total = 0
    for item in values:
        if item % 2 == 0:
            total += item
    return total
