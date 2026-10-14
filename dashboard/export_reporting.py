"""Export the dbt reporting tables from Athena into one DuckDB file.

The dashboard reads this file instead of querying Athena, so it can use a key
that only downloads one S3 object. Run daily in CI after the dbt build:

    python dashboard/export_reporting.py --upload s3://<bucket>/dashboard/spotify.duckdb

Locally (writes dashboard/spotify.duckdb):

    AWS_PROFILE=spotify-dev python dashboard/export_reporting.py
"""
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import boto3
import duckdb
from pyathena import connect
from pyathena.pandas.cursor import PandasCursor

REGION = "us-east-1"
DATABASE = "spotify_analytics"
TABLE_PREFIXES = ("agg_", "rpt_")
DEFAULT_STAGING = "s3://spotify-listening-history-767397767318-us-east-1-an/athena-results/"
DEFAULT_OUTPUT = Path(__file__).parent / "spotify.duckdb"


def reporting_tables():
    """Names of the reporting tables in Glue, so new agg_/rpt_ models are picked up."""
    glue = boto3.client("glue", region_name=REGION)
    names = []
    for page in glue.get_paginator("get_tables").paginate(DatabaseName=DATABASE):
        names += [t["Name"] for t in page["TableList"] if t["Name"].startswith(TABLE_PREFIXES)]
    return sorted(names)


def export(output: Path):
    tables = reporting_tables()
    if not tables:
        raise SystemExit(f"No {TABLE_PREFIXES} tables found in {DATABASE}")

    cursor = connect(
        s3_staging_dir=os.environ.get("DBT_S3_STAGING_DIR", DEFAULT_STAGING),
        region_name=REGION,
        cursor_class=PandasCursor,
    ).cursor()

    # build into a temp file so a failed export never leaves a half-written file
    tmp = output.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    for table in tables:
        df = cursor.execute(f"select * from {DATABASE}.{table}").as_pandas()
        # pandas turns Athena dates into timestamps; cast them back to DATE
        dates = [col[0] for col in cursor.description if col[1] == "date"]
        replace = f" replace ({', '.join(f'cast({c} as date) as {c}' for c in dates)})" if dates else ""
        con.register("df", df)
        con.execute(f"create table {table} as select *{replace} from df")
        con.unregister("df")
        print(f"{table}: {len(df)} rows")

    con.execute("create table export_info as select ?::timestamp as exported_at_utc",
                [datetime.now(timezone.utc).replace(tzinfo=None)])
    con.close()
    tmp.replace(output)
    print(f"Wrote {output}")


def upload(path: Path, s3_uri: str):
    uri = urlparse(s3_uri)
    boto3.client("s3", region_name=REGION).upload_file(str(path), uri.netloc, uri.path.lstrip("/"))
    print(f"Uploaded to {s3_uri}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--upload", metavar="S3_URI", help="also upload the file to this S3 URI")
    args = parser.parse_args()

    export(args.output)
    if args.upload:
        upload(args.output, args.upload)
