with source as (
    select
        *
    from {{ ref('stg_deezer__album_genres') }}
),

unnested_source as (
    select
        distinct genre
    from source
    cross join unnest(genres) as t(genre)
)


select 
    {{ dbt_utils.generate_surrogate_key(['genre']) }} as genre_id,
    genre
from unnested_source
