import json, urllib.request
import boto3

ssm = boto3.client("ssm")
_token = None

def get_token():
    global _token
    if _token is None:
        _token = ssm.get_parameter(
            Name="/github/spotify/access_token", WithDecryption=True
        )["Parameter"]["Value"]
    return _token

def lambda_handler(event, context):
    mode = event.get("mode", "full")
    req = urllib.request.Request(
        "https://api.github.com/repos/alavi-sam/spotify-stats/actions/workflows/dbt-production.yml/dispatches",
        data=json.dumps({"ref": "main", "inputs": {"mode": mode}}).encode(),
        headers={
            "Authorization": f"Bearer {get_token()}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "eventbridge-scheduler",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return {"status": resp.status, "mode": mode}  # 204 = dispatched