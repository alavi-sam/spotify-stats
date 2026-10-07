with source as (
    select * from {{ source('deezer_raw', 'album_genres') }}
),

ranked as (
    select
        *,
        row_number() over (partition by album_id order by fetched_at desc) as rn
    from source
)

select
    album_id,
    deezer_album_id,
    status,
    genres,
    fetched_at
from ranked
where rn = 1
