from web.config import get_settings
from web.app import slow_url
from celery.schedules import crontab


# pass in the task as a string to avoid circular imports
beat_schedule = {
    "get_slow_url": {
        "task": "web.celery_tasks.get_response",
        "schedule": crontab(minute="*/30"),
        "args": (slow_url, "slow_url"),
    }
}

task_time_to_live = 2 * 60 * 60  # 2 hours
task_time_limit = 600
task_track_started = True
worker_concurrency = 2

broker_url = get_settings().celery_dash_broker_url  # "redis://redis:6379/0"
result_backend = get_settings().celery_dash_result_backend  # "redis://redis:6379/0"

imports = ("web.celery_tasks",)

beat_schedule_filename = "celerybeat-schedule"
