import json

def handler(request):
    """
    Placeholder webhook endpoint.
    Akan diimplementasi di Phase 1A.
    """
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "ok"})
    }
