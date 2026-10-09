ALLOWED = {
    ("pending", "pay"): "paid",
    ("pending", "ship"): "shipped",
    ("paid", "ship"): "shipped",
    ("shipped", "deliver"): "delivered",
}

def transition(state, action):
    key = (state, action)
    if key not in ALLOWED:
        raise ValueError("illegal")
    return ALLOWED[key]
