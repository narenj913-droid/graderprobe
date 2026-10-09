def sum_evens(values):
    acc = 0
    for item in values:
        if item % 2 == 0:
            acc += item
    return acc
