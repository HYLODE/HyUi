from web.config import get_settings
from web.pages.demo import slow_url
from web import API_URLS, SITREP_DEPT2WARD_MAPPING
from celery.schedules import crontab
from web import ids as web_ids

campus_url = API_URLS.get("campus_url")


# using this dictionary to hold information about data stores
# pass in the task as a string to avoid circular imports
beat_schedule = {
    "get_slow_url": {
        "task": "web.celery_tasks.get_response",
        "schedule": crontab(minute="*/30"),
        "args": (
            slow_url,
            "slow_url",
        ),
        "kwargs": {"expires": 31 * 60},
    },
    "get_campus": {
        "task": "web.celery_tasks.get_response",
        "schedule": crontab(hour="*/12"),  # every 12 hours
        "args": (
            campus_url,
            "campus_url",
        ),
        "kwargs": {"expires": (12 * 3600) + 60},  # 12 hours + 1 minute
    },
    web_ids.DEPT_STORE: {
        "task": "web.celery_tasks.get_response",
        "schedule": crontab(minute=0, hour=0),  # daily at midnight
        "args": (
            API_URLS[web_ids.DEPT_STORE],
            web_ids.DEPT_STORE,
        ),
        "kwargs": {"expires": (24 * 3600) + 60},  # 24 hours + 1 minute
    },
    web_ids.ROOM_STORE: {
        "task": "web.celery_tasks.get_response",
        "schedule": crontab(minute=0, hour=0),  # daily at midnight
        "args": (
            API_URLS[web_ids.ROOM_STORE],
            web_ids.ROOM_STORE,
        ),
        "kwargs": {"expires": (24 * 3600) + 60},  # 24 hours + 1 minute
    },
    web_ids.BEDS_STORE: {
        "task": "web.celery_tasks.get_response",
        "schedule": crontab(minute=0, hour=0),  # daily at midnight
        "args": (
            API_URLS[web_ids.BEDS_STORE],
            web_ids.BEDS_STORE,
        ),
        "kwargs": {"expires": (24 * 3600) + 60},  # 24 hours + 1 minute
    },
    web_ids.ELECTIVES_STORE: {
        "task": "web.celery_tasks.get_response",
        "schedule": crontab(minute=0, hour=0),  # daily at midnight
        "args": (
            API_URLS[web_ids.ELECTIVES_STORE],
            web_ids.ELECTIVES_STORE,
        ),
        "kwargs": {"expires": (24 * 3600) + 60},  # 24 hours + 1 minute
    },
}


def _sitrep_store_url(icu):
    return f"{get_settings().api_url}/sitrep/live/{icu}/ui/"

# add tasks for all sitrep stores
for icu in list(SITREP_DEPT2WARD_MAPPING.values()):
    kkey = f"{web_ids.SITREP_STORE}-{icu}"
    url = _sitrep_store_url(icu)
    beat_schedule[kkey] = {
        "task": "web.celery_tasks.get_response",
        "schedule": crontab(minute="*/30"),  # every 30 minutes
        "args": (
            url,
            kkey,
        ),
        "kwargs": {"expires": (30 * 60) + 60},  # 30 mins + 1 minute
        # 'addons' holds additional data about the task
        "addons": {"icu": icu},
    }


# add tasks for all census work
# TODO: add tasks for all census work


task_time_to_live = 2 * 60 * 60  # 2 hours
task_time_limit = 600
task_track_started = True
worker_concurrency = 2

broker_url = get_settings().celery_dash_broker_url  # "redis://redis:6379/0"
result_backend = get_settings().celery_dash_result_backend  # "redis://redis:6379/0"

imports = ("web.celery_tasks",)

beat_schedule_filename = "celerybeat-schedule"
