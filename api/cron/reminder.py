import json

def handler(request):
    """
    Placeholder cron endpoint.
    Akan diimplementasi di Phase 1C.
    """
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "ok"})
    }
