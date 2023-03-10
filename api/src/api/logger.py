import notifiers
from loguru import logger
from notifiers.logging import NotificationHandler
from pathlib import Path
from api.config import get_settings
from datetime import datetime

# Log file
log_file = Path(__file__).parent / "api.log"
logger.add(log_file, rotation="5MB", retention="30 days", level="INFO")

# Slack notifications
slack_settings = {"webhook_url": get_settings().slack_log_webhook.get_secret_value()}
slack_bot = notifiers.get_notifier("slack")
slack_bot.notify(
    message=f"{datetime.now().isoformat()} | HyUi (API) logging started",
    **slack_settings,
)
slack_handler = NotificationHandler("slack", defaults=slack_settings)
logger.add(slack_handler, level="ERROR")

# Set-up complete
logger.success("API logging configured and running")
logger.info(
    "Log files exist within the docker container but can also be "
    "captured by redirecting at the commad line e.g."
    "docker-compose logs -f api > api.log 2>&1 &"
)
# https://stackoverflow.com/a/68960206/992999
