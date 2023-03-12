import functools
import notifiers
from loguru import logger
from notifiers.logging import NotificationHandler
from pathlib import Path
from api.config import get_settings
from datetime import datetime
import time
from collections.abc import Callable
from typing import TypeVar, ParamSpec

# Strategy to manage type checking
# https://stackoverflow.com/a/65602590/992999
T = TypeVar("T")
P = ParamSpec("P")


def logger_timeit(*, level: str = "DEBUG") -> Callable:
    """
    Decorator to log timings
    via https://loguru.readthedocs.io/en/stable/resources/recipes.html
    #logging-entry-and-exit-of-functions-with-a-decorator


    """

    def wrapper(func: Callable[P, T]) -> Callable[P, T]:
        name = func.__name__

        @functools.wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            logger_ = logger.opt(depth=1)
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            logger_.log(
                level, f"Function {name} returned in" f" {1000 * (end - start):.1f}ms"
            )
            return result

        return wrapped

    return wrapper


# Log file
log_file = Path(__file__).parent / "web.log"
logger.add(
    log_file,
    rotation="5MB",
    retention="30 days",
    level="INFO",
    backtrace=True,
    diagnose=True,
)

# Slack notifications
slack_settings = {"webhook_url": get_settings().slack_log_webhook.get_secret_value()}
slack_bot = notifiers.get_notifier("slack")
slack_bot.notify(
    message=f"{datetime.now().isoformat()} | HyUi (Web) logging started",
    **slack_settings,
)
slack_handler = NotificationHandler("slack", defaults=slack_settings)
logger.add(slack_handler, level="ERROR")

# Set-up complete
logger.success("Web logging configured and running")
logger.info(
    "Log files exist within the docker container but can also be "
    "captured by redirecting at the commad line e.g."
    "docker-compose logs -f web > web.log 2>&1 &"
)
# https://stackoverflow.com/a/68960206/992999
