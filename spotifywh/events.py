import datetime
import re

from spotivents import SpotifyAPIControllerClient, SpotifyClient
from spotivents.clustercls import SpotifyDeviceStateChangeCluster
from spotivents.constants import SPOTIVENTS_DEVICE_ID
from spotivents.utils import encode_bytes_to_basex

from .utils import fetch_playlist, fetch_user_me, get_spotify_url, query_entity_metadata

LIKED_PLAYLIST_REGEX = re.compile(r"spotify:user:.+?:collection")

SPOTIFY_ENTITY_REGEX = re.compile(r"^spotify:(?:user:)?(.+?):([a-zA-Z0-9]+)$")


def to_stringified_duration(duration_ms: int) -> str:
    minutes, seconds = divmod(duration_ms // 1000, 60)
    return f"{minutes}:{seconds:02}"


async def fetch_get_cluster_state(
    ws: SpotifyClient,
    controller: SpotifyAPIControllerClient,
    cluster: SpotifyDeviceStateChangeCluster,
    *,
    debug_mode: bool = False,
):
    user_data = await fetch_user_me(controller)

    fields = []

    if cluster.player_state is None or cluster.player_state.track is None:
        return

    track_uri = cluster.player_state.track.uri
    track_type_of, track_id = track_uri.split(":")[-2:]

    track_metadata = await query_entity_metadata(controller, track_id, track_type_of)

    if "album" in track_metadata:
        images = track_metadata["album"]["cover_group"]["image"]
    else:
        if "cover_image" in track_metadata:
            images = track_metadata["cover_image"]["image"]
        else:
            images = []

    if images:
        image = "https://i.scdn.co/image/" + images[-1]["file_id"]
    else:
        image = None

    if "artist" in track_metadata:
        artist_txt = ", ".join(
            f'[{artist["name"]}]({get_spotify_url("artist", encode_bytes_to_basex(bytes.fromhex(artist["gid"])))})'
            for artist in track_metadata["artist"]
        )
    else:
        if "show" in track_metadata:
            artist_txt = f'[{track_metadata["show"]["name"]}]({get_spotify_url("show", encode_bytes_to_basex(bytes.fromhex(track_metadata["show"]["gid"])))})'
        else:
            artist_txt = "Unknown artist"

    if cluster.devices:

        fields.append(
            {
                "name": "Available devices",
                "value": "\n".join(
                    f"{device.name or device_id}"
                    + (" - Private Session" if device.is_private_session else "")
                    + (
                        f" (Active, volume: {device.volume * 100 / 65565:.1f}%)"
                        if device_id == cluster.active_device_id
                        else ""
                    )
                    for device_id, device in cluster.devices.items()
                ),
                "inline": True,
            }
        )

    if cluster.player_state.context_uri is not None:

        in_user_collection = LIKED_PLAYLIST_REGEX.search(
            cluster.player_state.context_uri
        )

        context_uri_match = SPOTIFY_ENTITY_REGEX.search(
            cluster.player_state.context_uri
        )

        if context_uri_match is not None:
            type_of, uri = context_uri_match.groups()

            if uri != track_id:

                if type_of == "playlist":
                    data = await fetch_playlist(controller, uri)
                    context_name = f'[{data["name"]}]({get_spotify_url(type_of, uri)})\nby [{data["owner"]["display_name"]}]({get_spotify_url("user", data["owner"]["id"])})'
                else:
                    if in_user_collection is None:
                        context_metadata = await query_entity_metadata(
                            controller, uri, type_of
                        )
                        context_name = f"[{context_metadata['name']}]({get_spotify_url(type_of, uri)})"
                    else:
                        context_name = f"Liked Songs\nby [{user_data['display_name']}]({get_spotify_url('user', type_of)})"
                        type_of = "user collection"

                fields.append(
                    {
                        "name": f"Playing from {type_of}",
                        "value": context_name,
                        "inline": True,
                    }
                )

    if cluster.player_state.options is not None:

        texts = ()

        if cluster.player_state.options.repeating_track:
            texts += ("Repeating the track",)

        if cluster.player_state.options.repeating_context:
            texts += ("Repeating the context",)

        if cluster.player_state.options.shuffling_context:
            texts += ("Shuffling",)

        if texts:
            fields.append(
                {
                    "name": "Player Options",
                    "value": " & ".join(texts),
                    "inline": True,
                }
            )

    position = int(cluster.player_state.position_as_of_timestamp)
    duration = (
        int(cluster.player_state.duration)
        if cluster.player_state.duration is not None
        else None
    )

    description = (
        f"[{track_metadata['name']}]({get_spotify_url(track_type_of, track_id)}) by {artist_txt}\n"
        + (
            f"**{to_stringified_duration(position)}**/{to_stringified_duration(duration) if duration is not None else '--:--'}"
        )
    )

    timestamp = datetime.datetime.fromtimestamp(
        int(cluster.server_timestamp_ms) / 1000, datetime.timezone.utc
    )

    footer = {
        "text": f'{user_data["display_name"]}',
        "icon_url": user_data["images"][0]["url"] if user_data["images"] else None,
    }

    embeds = [
        {
            "title": "Now playing"
            if not cluster.player_state.is_paused
            else "Player paused",
            "description": description,
            "color": 0x1DB954,
            "thumbnail": {"url": image} if image is not None else None,
            "fields": fields,
            "timestamp": timestamp.isoformat(),
            "footer": footer,
        }
    ]

    if debug_mode:
        embeds.append(
            {
                "title": "Spotivents, for developers by developers",
                "description": (
                    f"Latency: `{ws.latency * 1000:.1f}`ms\n"
                    f"Most recent event: {f'`{ws.cluster.type}`' if ws.cluster else 'unavailable'}\n"
                    f"Spotivents device: `{SPOTIVENTS_DEVICE_ID}`\n"
                    f"Spotivents invisibility: {f'`{SPOTIVENTS_DEVICE_ID not in ws.cluster.devices}`'.lower() if ws.cluster else 'unavailable'}\n"
                ),
                "color": 0x1DB9C9,
                "timestamp": timestamp.isoformat(),
                "footer": {
                    "text": f"spotify-webhooks Debugging",
                },
            }
        )

    return {
        "embeds": embeds,
        "username": "Spotify",
        "avatar_url": "https://developer.spotify.com/assets/branding-guidelines/icon3@2x.png",
    }
