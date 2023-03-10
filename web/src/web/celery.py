import redis
from celery import Celery
from web.config import get_settings

# Redis client to hold the cache from slow callbacks
# NOTE: we are using a different redis database than the one used by celery
redis_client = redis.from_url(get_settings().redis_cache)  # "redis://redis:6379/1"

# celery app to manage tasks
celery_app = Celery("tasks")
celery_app.config_from_object("web.celery_config")
