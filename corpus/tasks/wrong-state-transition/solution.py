ALLOWED = {
    ("pending", "pay"): "paid",
    ("paid", "ship"): "shipped",
    ("shipped", "deliver"): "delivered",
}

def transition(state, action):
    key = (state, action)
    if key not in ALLOWED:
        raise ValueError("illegal")
    return ALLOWED[key]
