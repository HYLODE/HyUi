from web.logger import logger
from web.celery_tasks import get_response
from web.celery_config import beat_schedule


def run_startup_tasks() -> None:
    logger.info("Running startup tasks")
    for task, _conf in beat_schedule.items():
        logger.info(f"Running {task} task")
        get_response.apply_async(
            args=beat_schedule[task]["args"],
            kwargs=beat_schedule[task]["kwargs"],
        )
