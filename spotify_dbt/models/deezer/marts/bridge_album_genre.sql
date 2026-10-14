with genre as (
    select * from {{ ref('dim_genres') }}
),

source as (
    select distinct album_id, genre from {{ ref('stg_deezer__album_genres') }}
    cross join unnest(genres) as t(genre)
),

joined_tbl as (
    select 
        source.album_id,
        genre.genre_id
    from source
    join genre on genre.genre = source.genre
    -- only albums still in the warehouse (drops albums of excluded tracks)
    join {{ ref('dim_album') }} as album on album.album_id = source.album_id
)

select 
    {{ dbt_utils.generate_surrogate_key(['album_id', 'genre_id']) }} as album_genre_id,
    album_id,
    genre_id
from joined_tbl
