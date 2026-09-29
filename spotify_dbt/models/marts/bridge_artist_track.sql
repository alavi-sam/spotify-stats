with source as (
    SELECT
        DISTINCT
        track_id,
        artist_id,
        artist_position
    from {{ ref('stg_spotify__track_artists') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['track_id', 'artist_id']) }} as track_artist_id,
    track_id,
    artist_id,
    artist_position
from source


