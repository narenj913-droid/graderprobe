def even(item):
    return item % 2 == 0

def sum_evens(values):
    return sum(item for item in values if even(item))
