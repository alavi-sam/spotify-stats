# spotify_dbt

This directory contains the dbt transformation project for the Spotify Listening History Warehouse.

For the complete architecture, AWS setup, Lambda deployment, GitHub Actions configuration, model documentation, and troubleshooting guide, see the [repository README](../README.md).

## Quick start

```bash
python -m pip install --requirement requirements.txt
dbt deps
dbt debug
dbt build
```

The project uses Athena, the AWS Glue Data Catalog, S3-backed tables, and an incremental Iceberg `fct_plays` model. Local AWS credentials belong in `~/.aws` and `~/.dbt/profiles.yml`; do not commit them to this directory.
