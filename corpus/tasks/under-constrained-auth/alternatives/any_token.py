SECRET = "s3cret"

def lookup(record, token):
    if not token:
        raise PermissionError("denied")
    return record["payload"]
