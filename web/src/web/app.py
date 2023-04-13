import dash
from dash import CeleryManager

from pathlib import Path
from web.config import get_settings
from web.layout.appshell import create_appshell
from web.logger import logger
from celery import Celery, shared_task

logger.info("Web app starting")

background_cache_expire = 600  # seconds
logger.info(
    f"Background callbacks cache expiration default {background_cache_expire} "
    f"seconds"
)

# TODO: fix temporary hard coding
broker_url = "redis://redis:6379/0"
result_backend = "redis://redis:6379/0"
celery = Celery(
    __name__,
    broker=broker_url,
    backend=result_backend,
)
# celery.config_from_object('celeryconfig')

background_callback_manager = CeleryManager(celery)

with Path(__file__).parent / "index.html" as f:
    index_string = f.open().read()

FONTS_GOOGLE = "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap"
FONTS_FA = "https://use.fontawesome.com/releases/v5.8.1/css/all.css"

app = dash.Dash(
    __name__,
    use_pages=True,
    # external_scripts=external_scripts,
    external_stylesheets=[
        "assets/style.css",
        FONTS_GOOGLE,
        FONTS_FA,
    ],
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, maximum-scale=1, "
            "user-scalable=no",
        }
    ],
    background_callback_manager=background_callback_manager,
    index_string=index_string,
)

app.config.suppress_callback_exceptions = True
app.layout = create_appshell([dash.page_registry.values()])

server = app.server

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=get_settings().development_port, debug=True)
