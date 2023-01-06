import dash

from web.layout.appshell import create_appshell
from web.config import get_settings

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
)

app.config.suppress_callback_exceptions = True
app.layout = create_appshell([dash.page_registry.values()])

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=get_settings().development_port, debug=True)
