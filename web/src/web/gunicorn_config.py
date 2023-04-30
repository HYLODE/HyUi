from os import getenv
from web.logger import logger

if getenv("DEBUG") == "1":
    logger.info("Debug mode enabled for Gunicorn (incl hot reload)")
    debug = True

bind = "0.0.0.0:8000"
reload = True if debug else False
timeout = 60 * 60  # 1 hour
workers = 1
worker_class = "gevent"
