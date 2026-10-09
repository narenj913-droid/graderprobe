EDGES = {
    ("pending", "pay"): "paid",
    ("paid", "ship"): "shipped",
    ("shipped", "deliver"): "delivered",
}

def transition(state, action):
    key = (state, action)
    if key not in EDGES:
        raise ValueError("illegal")
    return EDGES[key]
