SELECT
    f.play_id,
    f.track_id,
    f.album_id
from {{ ref('fct_plays') }} as f
where not exists (
    select
        1
    from {{ ref('dim_track') }} as b
    where b.track_id = f.track_id
    and b.album_id = f.album_id
)