def transition(state, action):
    graph = {
        "pending": {"pay": "paid"},
        "paid": {"ship": "shipped"},
        "shipped": {"deliver": "delivered"},
    }
    nxt = graph.get(state, {}).get(action)
    if nxt is None:
        raise ValueError("illegal")
    return nxt
