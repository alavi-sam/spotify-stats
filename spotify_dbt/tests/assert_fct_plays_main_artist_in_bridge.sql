SELECT
    f.play_id,
    f.track_id,
    f.main_artist_id
from {{ ref('fct_plays') }} as f
where not exists (
    select
        1
    from {{ ref('bridge_artist_track') }} as b
    where b.track_id = f.track_id
    and b.artist_id = f.main_artist_id
    and b.artist_position = 1
)