{{ config(
    materialized='incremental',
    table_type='iceberg',
    incremental_strategy='merge',
    unique_key='play_id',
    partitioned_by=['month(played_at_local)'],
    table_properties={'vacuum_max_snapshot_age_seconds': 604800},
    post_hook=[
        "{% if var('iceberg_maintenance', false) %}optimize {{ this.render_pure() }} rewrite data using bin_pack{% endif %}",
        "{% if var('iceberg_maintenance', false) %}vacuum {{ this.render_pure() }}{% endif %}"
    ]
) }}

with source as (
    SELECT
        *
    from {{ ref('stg_spotify__plays') }}
)

select
    play_id,
    album_id,
    element_at(artists, 1).id as main_artist_id,
    track_id,
    context_type,
    duration_ms,
    played_at_local,
    played_at_utc,
    cast(played_at_local as date) as play_date_local,
    partition_date
from source

{% if is_incremental() %}
where played_at_utc > (
        select max(played_at_utc) - interval '1' day from {{ this }}
    )
  and partition_date >= (
        select cast(date_add('day', -2, max(play_date_local)) as varchar) from {{ this }}
    )
{% endif %}