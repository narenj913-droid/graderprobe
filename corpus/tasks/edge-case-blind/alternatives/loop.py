def maximum(values):
    if not values:
        raise ValueError("empty")
    best = values[0]
    for item in values[1:]:
        if item > best:
            best = item
    return best
