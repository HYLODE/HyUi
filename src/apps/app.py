# src/apps/app.py
"""
The application itself
"""
import dash_bootstrap_components as dbc
from dash import Dash, page_container, page_registry

from config import settings

BPID = "app_"
CORE_PAGES = ["Home", "Sitrep", "Electives"]

app = Dash(
    __name__,
    title="HyUi",
    update_title=None,
    external_stylesheets=[
        dbc.themes.SIMPLEX,
        dbc.icons.FONT_AWESOME,
    ],
    suppress_callback_exceptions=True,
    use_pages=True,
)


def other_pages_dropdown():
    dropdown = []
    for page in page_registry.values():
        if page["name"] in CORE_PAGES:
            continue
        dropdown.append(dbc.DropdownMenuItem(page["name"], href=page["path"]))
    return dropdown


navbar = dbc.NavbarSimple(
    children=[
        dbc.Nav(
            [
                dbc.NavLink(page["name"], href=page["path"])
                for page in page_registry.values()
                if page["name"] in CORE_PAGES
            ],
        ),
        dbc.DropdownMenu(
            children=other_pages_dropdown(),
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand="HYLODE",
    sticky="top",
    class_name="mb-2",
)

app.layout = dbc.Container(
    [
        navbar,
        dbc.Row([page_container]),
    ],
    fluid=True,
    className="dbc",
)


# standalone apps : please use ports fastapi 8092 and dash 8093
# this is the callable object run by gunicorn
# cd ./src/
# gunicorn -w 4 --bind 0.0.0.0:8093 apps.app:server
server = app.server


# this is the application run in development
# cd ./src/
# python apps/app.py
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=settings.PORT_COMMANDLINE_APP, debug=True)
