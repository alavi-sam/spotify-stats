with track_artists as (
    select
        b.track_id,
        array_join(array_agg(a.artist_name order by b.artist_position), ', ') as all_artist_names
    from {{ ref('bridge_artist_track') }} as b
    join {{ ref('dim_artist') }} as a on a.artist_id = b.artist_id
    group by b.track_id
),

album_genres as (
    select
        b.album_id,
        array_join(array_agg(g.genre order by g.genre), ', ') as genres
    from {{ ref('bridge_album_genre') }} as b
    join {{ ref('dim_genres') }} as g on g.genre_id = b.genre_id
    group by b.album_id
)

select
    p.play_id,
    cast(p.played_at_local as timestamp(3))     as played_at_local,
    cast(p.played_at_utc as timestamp(3))       as played_at_utc,
    p.play_date_local,
    hour(p.played_at_local)                     as hour_of_day,
    d.day_of_week,
    d.day_name,
    d.is_weekend,
    p.track_id,
    t.track_name,
    p.duration_ms,
    t.explicit,
    p.album_id,
    al.album_name,
    al.album_type,
    al.release_date,
    al.album_image_url,
    p.main_artist_id,
    ar.artist_name                              as main_artist_name,
    ta.all_artist_names,
    coalesce(ag.genres, 'Unknown')              as genres,
    p.context_type.type                         as context_type
from {{ ref('fct_plays') }} as p
left join {{ ref('dim_date') }} as d on d.date_day = p.play_date_local
left join {{ ref('dim_track') }} as t on t.track_id = p.track_id
left join {{ ref('dim_album') }} as al on al.album_id = p.album_id
left join {{ ref('dim_artist') }} as ar on ar.artist_id = p.main_artist_id
left join track_artists as ta on ta.track_id = p.track_id
left join album_genres as ag on ag.album_id = p.album_id
