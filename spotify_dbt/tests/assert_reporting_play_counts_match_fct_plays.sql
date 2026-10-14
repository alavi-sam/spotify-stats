with expected as (
    select count(*) as play_count from {{ ref('fct_plays') }}
),

actual as (
    select 'agg_daily_listening' as model, sum(play_count) as play_count from {{ ref('agg_daily_listening') }}
    union all
    select 'agg_daily_track_plays', sum(play_count) from {{ ref('agg_daily_track_plays') }}
    union all
    select 'agg_daily_artist_plays', sum(play_count) from {{ ref('agg_daily_artist_plays') }}
    union all
    select 'agg_listening_by_weekday_hour', sum(play_count) from {{ ref('agg_listening_by_weekday_hour') }}
    union all
    select 'rpt_plays_enriched', count(*) from {{ ref('rpt_plays_enriched') }}
)

select
    a.model,
    a.play_count as actual_play_count,
    e.play_count as expected_play_count
from actual as a
cross join expected as e
where a.play_count <> e.play_count
