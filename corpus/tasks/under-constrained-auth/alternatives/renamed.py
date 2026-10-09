SECRET = "s3cret"

def lookup(record, credential):
    if credential != SECRET:
        raise PermissionError("denied")
    return record["payload"]
