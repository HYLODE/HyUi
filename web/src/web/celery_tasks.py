import requests
import orjson
from web.celery import celery_app, redis_client


@celery_app.task
def get_response(url, cache_key):
    """
    Get a response from a URL
    """
    response = requests.get(url)
    data = response.json()
    redis_client.set(cache_key, orjson.dumps(data))
    redis_client.expire(cache_key, 5 * 60)  # 5 minutes
    return data
