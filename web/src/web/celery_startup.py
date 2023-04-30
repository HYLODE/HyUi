from web.logger import logger
from web.celery_tasks import get_response
from web.celery_config import beat_schedule


def run_startup_tasks():
    logger.info("Running startup tasks")
    get_response.apply_async(
        args=beat_schedule["get_campus"]["args"],
        kwargs=beat_schedule["get_campus"]["kwargs"],
    )
