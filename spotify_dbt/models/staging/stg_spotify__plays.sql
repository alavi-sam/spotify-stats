select
    track.name as track_name,
    played_at
from {{ source('spotify_raw', 'recently_played') }}
