import dash

import diskcache
import tempfile
from uuid import uuid4
from web.layout.appshell import create_appshell
from web.config import get_settings

launch_uuid = uuid4()
cache = diskcache.Cache(tempfile.TemporaryDirectory().name)
background_callback_manager = dash.DiskcacheManager(
    cache, cache_by=[lambda: launch_uuid], expire=600  # seconds
)

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        "assets/style.css",
        # include google fonts
        "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400"
        ";500;900&display=swap",
        "https://use.fontawesome.com/releases/v5.8.1/css/all.css",
    ],
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, maximum-scale=1, "
            "user-scalable=no",
        }
    ],
    background_callback_manager=background_callback_manager,
)

app.config.suppress_callback_exceptions = True
app.layout = create_appshell([dash.page_registry.values()])

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=get_settings().development_port, debug=True)
