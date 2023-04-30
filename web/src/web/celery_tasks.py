# NOTE: changing the name of this file will require you to change all the ./docker/celery/start-* scripts
import requests
import orjson
from web.celery import celery_app, redis_client


@celery_app.task
def get_response(url, cache_key, expires: int = 3600):
    """
    Get a response from a URL
    """
    response = requests.get(url)
    data = response.json()
    redis_client.set(cache_key, orjson.dumps(data))
    # Remember to expire the cache just after the task refresh interval
    redis_client.expire(cache_key, expires)
    return data
