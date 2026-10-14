-- Every play counts for at least one genre ('Unknown' included), so each
-- day's genre plays must be at least that day's total plays.
with genre_daily as (
    select
        play_date_local,
        sum(play_count) as genre_play_count
    from {{ ref('agg_daily_genre_plays') }}
    group by play_date_local
)

select
    d.date_day,
    d.play_count,
    coalesce(g.genre_play_count, 0) as genre_play_count
from {{ ref('agg_daily_listening') }} as d
left join genre_daily as g on g.play_date_local = d.date_day
where coalesce(g.genre_play_count, 0) < d.play_count
