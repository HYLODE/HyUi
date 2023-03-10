import dash
from dash import CeleryManager
from flask import Flask

import web

from web.celery import celery_app
from web.celery_startup import run_startup_tasks
from web.config import get_settings
from web.debugger import initialize_flask_server_debugger_if_needed
from web.layout.appshell import create_appshell
from web.logger import logger

initialize_flask_server_debugger_if_needed()

server = Flask(__name__)

celery_manager = CeleryManager(celery_app)

# run celery startup tasks
run_startup_tasks()

logger.info("Starting the Dash application")
app = dash.Dash(
    __name__,
    # It is recommended to add __name__ to the Dash constructor to ensure the
    # resources in the assets folder are loaded (app = dash.Dash(__name__,
    # meta_tags=[...])). When you run your app through some other command line
    # (like the Flask command or Gunicorn/Waitress), the __main__ module will no
    # longer be located where app.py is. By explicitly setting __name__, Dash
    # will be able to locate the relative assets folder correctly.
    server=server,
    background_callback_manager=celery_manager,
    use_pages=True,
    external_stylesheets=[
        # do NOT need to include this; all .css files in ./assets will be loaded
        # "assets/style.css",
        web.FONTS_GOOGLE,
        web.FONTS_FA,
    ],
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, maximum-scale=1, "
            "user-scalable=no",
        }
    ],
    index_string=web.INDEX_STRING,
)

# Buld layout from page registry
app.layout = create_appshell([dash.page_registry.values()])

# set debug UI settings on/off when running under gunicorn
if get_settings().debug:
    logger.info("DEBUGGING configuration ON")
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_hot_reload=False)

# further app config
app.config.suppress_callback_exceptions = True

# expose application's object server so wsgi server can access it
server = app.server

if __name__ == "__main__":
    logger.info("Running with the local dash development server")
    debug = True if get_settings().debug else False
    app.run_server(host="0.0.0.0", port=get_settings().development_port, debug=debug)
