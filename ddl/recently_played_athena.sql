CREATE EXTERNAL TABLE if not exists spotify_raw.recently_played (
    track struct<
        album: struct<
            album_type: string,
            artists: array<
                struct<
                    external_urls: map<string, string>,
                    href: string,
                    id: string,
                    name: string,
                    type: string
                >
            >,
            external_urls: map<string, string>,
            href: string,
            id: string,
            images: array<
                struct<
                    url: string,
                    width: int,
                    height: int
                >
            >,
            is_playable: boolean,
            name: string,
            release_date: string,
            release_date_precision: string,
            total_tracks: int,
            type: string
        >,
        artists: array<
            struct<
                external_urls: map<string, string>,
                href: string,
                id: string,
                name: string,
                type: string
            >
        >,
        disc_number: int,
        duration_ms: int,
        explicit: boolean,
        external_ids: map<string, string>,
        external_urls: map<string, string>,
        href:string,
        id: string,
        is_local: boolean,
        is_playable: boolean,
        name: string,
        track_number: int,
        type: string
    >,
    played_at string,
    context struct<
        type: string,
        href: string
    >
)

partitioned by (dt string)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
location 's3://spotify-listening-history-767397767318-us-east-1-an/raw/spotify/recently_played/'
tblproperties(
    'projection.enabled' = 'true',
    'projection.dt.type' = 'date',
    'projection.dt.format' = 'yyyy-MM-dd',
    'projection.dt.range' = '2026-09-20,NOW',
    'storage.location.template' = 's3://spotify-listening-history-767397767318-us-east-1-an/raw/spotify/recently_played/dt=${dt}/'
)