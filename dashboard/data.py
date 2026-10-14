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
    path = LOCAL_FILE
    if not path.exists():
        aws = st.secrets["aws"]
        s3 = boto3.client(
            "s3",
            region_name=aws.get("region", "us-east-1"),
            aws_access_key_id=aws["access_key_id"],
            aws_secret_access_key=aws["secret_access_key"],
        )
        path = Path(tempfile.gettempdir()) / "spotify.duckdb"
        s3.download_file(aws["bucket"], aws["key"], str(path))
    return duckdb.connect(str(path), read_only=True)


@st.cache_data(ttl="1h", show_spinner=False)
def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    # one cursor per call: DuckDB connections aren't safe to share across sessions
    return _connection().cursor().execute(sql, list(params)).df()
