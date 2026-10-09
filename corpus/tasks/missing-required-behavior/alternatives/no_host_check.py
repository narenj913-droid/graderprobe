def parse_config(data):
    allowed = {"host", "port"}
    extra = set(data) - allowed
    if extra:
        raise ValueError("unknown")
    port = int(data.get("port", 80))
    return {"host": str(data.get("host", "")), "port": port}
