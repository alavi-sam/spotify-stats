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