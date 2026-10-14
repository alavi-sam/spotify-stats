-- A play counts once for every genre of its album, so genre totals can
-- exceed total plays. Albums Deezer has no genre for fall under 'Unknown'.
with play_genres as (
    select
        p.play_date_local,
        p.track_id,
        p.duration_ms,
        coalesce(g.genre_id, 'unknown')     as genre_id,
        coalesce(g.genre, 'Unknown')        as genre
    from {{ ref('fct_plays') }} as p
    left join {{ ref('bridge_album_genre') }} as b on b.album_id = p.album_id
    left join {{ ref('dim_genres') }} as g on g.genre_id = b.genre_id
)

select
    play_date_local,
    genre_id,
    genre,
    count(*)                                    as play_count,
    round(sum(duration_ms) / 60000.0, 1)        as est_minutes_played,
    count(distinct track_id)                    as distinct_tracks
from play_genres
group by play_date_local, genre_id, genre
