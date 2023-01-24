import asyncio
import os
import sys

import aiohttp
import dotenv
from spotivents import SpotifyAPIControllerClient, SpotifyAuthenticator, SpotifyClient
from spotivents.clustercls import SpotifyDeviceStateChangeCluster

from spotifywh.events import fetch_get_cluster_state

dotenv.load_dotenv()


SPOTIFY_COOKIE = os.getenv("SPOTIFY_COOKIE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


DEBUG_MODE = any((arg in sys.argv for arg in ("--debug", "-d")))
INVISIBLE_MODE = any((arg in sys.argv for arg in ("--invisible", "-i")))


assert SPOTIFY_COOKIE is not None, "SPOTIFY_COOKIE is not set"
assert WEBHOOK_URL is not None, "WEBHOOK_URL is not set"


async def main():

    session = aiohttp.ClientSession()

    auth = SpotifyAuthenticator(session, SPOTIFY_COOKIE)
    spotify_ws = SpotifyClient(session, auth)
    controller = SpotifyAPIControllerClient(session, auth)

    class SpotifyWebhook:
        def __init__(self, webhook_url):
            self.webhook_url = webhook_url

            self.message_id = None

    wh = SpotifyWebhook(WEBHOOK_URL)

    @spotify_ws.on_cluster_receive()
    async def on_receive(cluster: SpotifyDeviceStateChangeCluster):
        data = await fetch_get_cluster_state(
            spotify_ws, controller, cluster, debug_mode=DEBUG_MODE
        )

        if wh.message_id is not None:
            async with session.patch(
                f"{wh.webhook_url}/messages/{wh.message_id}",
                json=data,
            ) as response:
                ...
        else:
            async with session.post(
                wh.webhook_url,
                params={"wait": "true"},
                json=data,
            ) as response:
                wh.message_id = (await response.json())["id"]

    await spotify_ws.run(is_invisible=INVISIBLE_MODE)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
