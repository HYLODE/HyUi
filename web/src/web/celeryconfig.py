import os

# Need to stop hard coding and move these into a config
broker_url = "redis://redis:6379/0"
result_backend = "redis://redis:6379/0"

# CELERY_BROKER_URL=redis://redis:6379/0
# CELERY_RESULT_BACKEND=redis://redis:6379/0
# broker_url = os.environ['CELERY_BROKER_URL'],
# result_backend = os.environ['CELERY_RESULT_BACKEND']

# beat_schedule = {
#     "task-schedule-work": {
#         "task": "task_schedule_work",
#         "schedule": 5.0,  # five seconds
#     }
# }
