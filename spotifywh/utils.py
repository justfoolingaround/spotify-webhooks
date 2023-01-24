import asyncio
import functools


def get_spotify_url(entity_type, entity_id):
    return f"https://open.spotify.com/{entity_type}/{entity_id}"


class HashableDict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


def async_lru_cache(*lru_cache_args, **lru_cache_kwargs):
    def async_lru_cache_decorator(async_function):
        @functools.lru_cache(*lru_cache_args, **lru_cache_kwargs)
        def cached_async_function(*args, **kwargs):
            coroutine = async_function(*args, **kwargs)
            return asyncio.ensure_future(coroutine)

        return cached_async_function

    return async_lru_cache_decorator


@async_lru_cache()
async def query_entity_metadata(controller, entity_id, entity_type):
    return HashableDict(await controller.query_entity_metadata(entity_id, entity_type))


@async_lru_cache()
async def fetch_playlist(controller, playlist_id):
    async with controller.session.get(
        f"https://api.spotify.com/v1/playlists/{playlist_id}",
        headers=await controller.get_headers(),
    ) as response:
        return HashableDict(await response.json())


@async_lru_cache()
async def fetch_user_me(controller):
    async with controller.session.get(
        "https://api.spotify.com/v1/me",
        headers=await controller.get_headers(),
    ) as response:
        return HashableDict(await response.json())
