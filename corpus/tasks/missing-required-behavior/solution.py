def parse_config(data):
    allowed = {"host", "port"}
    extra = set(data) - allowed
    if extra:
        raise ValueError("unknown")
    if "host" not in data:
        raise ValueError("host")
    port = int(data.get("port", 80))
    return {"host": str(data["host"]), "port": port}
