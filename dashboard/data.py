"""Reads the reporting data that the daily CI export uploads to S3.

Locally the app uses dashboard/spotify.duckdb (made by export_reporting.py).
Deployed, it downloads that file with a key that can only read that one object.
"""
import tempfile
from pathlib import Path

import boto3
import duckdb
import pandas as pd
import streamlit as st

LOCAL_FILE = Path(__file__).parent / "spotify.duckdb"


@st.cache_resource(ttl="1h", show_spinner="Loading listening data…")
def _connection():
    """The open database and a version string that changes with every export."""
    path = LOCAL_FILE
    version = f"local-{path.stat().st_mtime_ns}" if path.exists() else None
    if not path.exists():
        aws = st.secrets["aws"]
        s3 = boto3.client(
            "s3",
            region_name=aws.get("region", "us-east-1"),
            aws_access_key_id=aws["access_key_id"],
            aws_secret_access_key=aws["secret_access_key"],
        )
        # One file per export: DuckDB reuses an open database for a path it has
        # seen, so re-downloading over the same path kept serving the old data.
        etag = s3.head_object(Bucket=aws["bucket"], Key=aws["key"])["ETag"].strip('"')
        path = Path(tempfile.gettempdir()) / f"spotify-{etag}.duckdb"
        if not path.exists():
            s3.download_file(aws["bucket"], aws["key"], str(path))
            for old in path.parent.glob("spotify-*.duckdb"):
                if old != path:
                    old.unlink(missing_ok=True)
        version = etag
    return duckdb.connect(str(path), read_only=True), version


def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    return _cached_query(_connection()[1], sql, params)


# keyed on the export version, so results from an older export are never reused
@st.cache_data(max_entries=256, show_spinner=False)
def _cached_query(version: str, sql: str, params: tuple) -> pd.DataFrame:
    # one cursor per call: DuckDB connections aren't safe to share across sessions
    return _connection()[0].cursor().execute(sql, list(params)).df()
