SECRET = "s3cret"

def authorized(token):
    return token == SECRET

def lookup(record, token):
    if not authorized(token):
        raise PermissionError("denied")
    return record["payload"]
