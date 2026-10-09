SECRET = "s3cret"

def lookup(record, token):
    if token != SECRET:
        raise PermissionError("denied")
    return record["payload"]
