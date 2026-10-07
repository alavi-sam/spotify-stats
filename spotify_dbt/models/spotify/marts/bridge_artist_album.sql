with source as (
    SELECT
        DISTINCT
        album_id,
        artist_id,
        artist_position
    from {{ ref('stg_spotify__album_artists') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['album_id', 'artist_id']) }} as album_artist_id,
    album_id,
    artist_id,
    artist_position
from source