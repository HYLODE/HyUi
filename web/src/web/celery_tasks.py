# NOTE: changing the name of this file will require you to
# change all the ./docker/celery/start-* scripts
import hashlib
import re

import orjson
import requests
from typing import Optional, Any

from web.celery import celery_app, redis_client
from web.logger import logger


@celery_app.task
def get_response(
    url: str, cache_key: str, params: Optional[dict] = None, expires: int = 3600
) -> tuple[object, int]:
    """
    Get a response from a URL
    TODO: might be best to take the logic below and
    include here so that all tasks can generate their own keys if needed
    """
    try:
        assert type(url) is str
    except AssertionError as e:
        logger.error(f"Invalid URL: {url} - {e}")
        return None, 400

    if params is None:
        logger.info(f"Fetching {url} - no parameters provided")
        response = requests.get(url)
    else:
        logger.info(f"Fetching {url} - params {str(params)[:16]} ...")
        response = requests.get(url, params=params)

    if response.status_code != 200:
        logger.error(f"Error fetching {url}: {response.status_code}")
        return None, response.status_code

    data = response.json()  # type: tuple[object, int]
    redis_client.set(cache_key, orjson.dumps(data))
    # Remember to expire the cache just after the task refresh interval
    redis_client.expire(cache_key, expires)

    return data


def replace_alphanumeric(s: str, replacement: str = "_") -> str:
    return re.sub(r"\W+", replacement, s)


def requests_try_cache(
    url: str,
    cache_key: Optional[str] = None,
    params: Optional[dict] = None,
    expires: Optional[int] = None,
) -> Any:
    """
    Drop in replacement for requests.get() that caches the response using redis;
    the idea is that I can just use this and it will generate a suitable cache
    key etc automatically from the URL

    Crucially this should mean that it's easy to cache anything since the URL is unique
    TODO: scheduling to keep the cache warm
    - prob need a sister function that cycles through URLs and prepopulates the cache
    """
    cache_key = replace_alphanumeric(url)
    if params:
        params_suffix = "_PARAMS_" + replace_alphanumeric(str(params))
        # Try to keep the cache key up somewhat limited in size
        # https://stackoverflow.com/a/30271837/992999
        if len(params_suffix) > 64:
            sha256 = hashlib.sha256()
            sha256.update(params_suffix.encode("utf-8"))
            cache_key = cache_key + params_suffix[:32] + sha256.hexdigest()
        else:
            cache_key = cache_key + params_suffix
    expires = 3600 if expires is None else expires

    cached_data = redis_client.get(cache_key)

    if cached_data is None:
        logger.info(f"Cache miss for {url} ... requesting")
        # Do not use the apply_async method from the celery_app.task decorator
        # because the function will return with nothing
        data = get_response(url, cache_key, params=params, expires=expires)
    else:
        logger.info(f"Cache hit for {url}")
        data = orjson.loads(cached_data)

    return data
