with source as (
    select
        *
    from {{ ref('stg_spotify__plays') }}
)

select
    distinct
    track_id,
    track_name,
    album_id,
    track_type,
    duration_ms,
    track_disc_number,
    explicit,
    element_at(track_external_urls, 'spotify') as track_url,
    is_track_local,
    is_track_playable,
    track_number    
from source
