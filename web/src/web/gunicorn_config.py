from gevent import monkey
from os import getenv
from web.logger import logger

# NOTE: Attempt to fix the warning
# ggevent.py:38: MonkeyPatchWarning: Monkey-patching
# ssl after ssl has already been imported may lead to errors
# via https://stackoverflow.com/a/74817491/992999
monkey.patch_all(thread=False, select=False)


if getenv("DEBUG") == "1":
    logger.info("Debug mode enabled for Gunicorn (incl hot reload)")
    debug = True
else:
    debug = False

bind = "0.0.0.0:8000"
reload = True if debug else False
timeout = 60 * 60  # 1 hour
workers = 1
worker_class = "gevent"
