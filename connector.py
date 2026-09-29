"""AWS Lambda entry point for ingesting Spotify recently played tracks into S3."""

import json
import os
from datetime import datetime, timezone
from typing import Any

import boto3
import requests


REQUEST_TIMEOUT_SECONDS = 15

ssm_client = boto3.client("ssm")
s3_client = boto3.client("s3")


class SpotifyAuthError(Exception):
    """Raised when Spotify token refresh or authentication fails."""


class SpotifyAPIError(Exception):
    """Raised when the Spotify Web API returns an unsuccessful response."""


def required_environment_variable(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def parameter_name(name: str) -> str:
    prefix = required_environment_variable("SSM_PREFIX").rstrip("/")
    return f"{prefix}/{name.lstrip('/')}"


def get_parameter(name: str, is_secure: bool = False) -> str:
    parameter = ssm_client.get_parameter(
        Name=parameter_name(name),
        WithDecryption=is_secure,
    )
    return parameter["Parameter"]["Value"]


def update_parameter(name: str, value: str, is_secure: bool = False) -> None:
    ssm_client.put_parameter(
        Name=parameter_name(name),
        Overwrite=True,
        Value=value,
        Type="SecureString" if is_secure else "String",
    )


def refresh_access_token() -> dict[str, Any]:
    response = requests.post(
        url="https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "client_id": get_parameter("client_id", is_secure=True),
            "client_secret": get_parameter("client_secret", is_secure=True),
            "refresh_token": get_parameter("refresh_token", is_secure=True),
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code >= 400:
        raise SpotifyAuthError(
            f"Spotify token refresh failed with status {response.status_code}"
        )

    payload = response.json()
    if "access_token" not in payload:
        raise SpotifyAuthError("Spotify token response did not contain an access token")

    return payload


def get_recently_played() -> dict[str, Any]:
    token_payload = refresh_access_token()

    if "refresh_token" in token_payload:
        update_parameter(
            "refresh_token",
            token_payload["refresh_token"],
            is_secure=True,
        )

    response = requests.get(
        url="https://api.spotify.com/v1/me/player/recently-played",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
        params={"limit": 50, "after": get_parameter("cursor")},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code in (401, 403):
        raise SpotifyAuthError(
            f"Spotify recently-played authentication failed with status "
            f"{response.status_code}"
        )
    if response.status_code >= 400:
        raise SpotifyAPIError(
            f"Spotify recently-played request failed with status {response.status_code}"
        )

    return response.json()


def put_item(item: dict[str, Any]) -> None:
    played_at = item["played_at"]
    partition_date = played_at.split("T", maxsplit=1)[0]
    played_at_timestamp = datetime.fromisoformat(played_at.replace("Z", "+00:00"))

    if played_at_timestamp.tzinfo is None:
        played_at_timestamp = played_at_timestamp.replace(tzinfo=timezone.utc)

    played_at_epoch_ms = int(played_at_timestamp.timestamp() * 1000)
    raw_prefix = required_environment_variable("RAW_PREFIX").strip("/")
    object_key = f"{raw_prefix}/dt={partition_date}/{played_at_epoch_ms}.json"

    s3_client.put_object(
        Bucket=required_environment_variable("RAW_BUCKET"),
        Key=object_key,
        Body=json.dumps(item).encode("utf-8"),
        ContentType="application/json",
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Fetch new Spotify plays, persist them to S3, and advance the cursor."""

    response = get_recently_played()
    items = response.get("items", [])

    for item in items:
        put_item(item)

    cursors = response.get("cursors") or {}
    if cursors.get("after"):
        update_parameter("cursor", cursors["after"])

    result = {"added_items": len(items)}
    print(json.dumps({"event": "spotify_ingestion_complete", **result}))

    return {
        "statusCode": 200,
        "body": json.dumps(result),
    }
