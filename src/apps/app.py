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
        dbc.themes.YETI,
        dbc.icons.FONT_AWESOME,
    ],
    suppress_callback_exceptions=True,
    use_pages=True,
)


def header_pages_dropdown():
    """Filters and sorts pages from registry for display in main navbar"""
    pp = {page["name"]: page["path"] for page in page_registry.values()}
    ll = []
    for page in CORE_PAGES:
        ll.append(dbc.NavItem(dbc.NavLink(page, href=pp[page])))
    return ll


def more_pages_dropdown():
    """Filters and sorts pages from registry for dropdown"""
    pp = [dbc.DropdownMenuItem("Additional reports", header=True)]
    for page in page_registry.values():
        if page["name"] in CORE_PAGES:
            continue
        pp.append(dbc.DropdownMenuItem(page["name"], href=page["path"]))
    return pp


navbar = dbc.NavbarSimple(
    children=[
        dbc.Nav(children=header_pages_dropdown()),
        dbc.DropdownMenu(
            children=more_pages_dropdown(),
            nav=True,
            in_navbar=True,
            label="More",
        ),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Developer Tools", header=True),
                dbc.DropdownMenuItem("HYLODE", href="http://172.16.149.202:5001/"),
                dbc.DropdownMenuItem("HYMIND Lab", href="http://172.16.149.202:5009/"),
                dbc.DropdownMenuItem("HYUI API", href="http://172.16.149.202:8094/"),
                dbc.DropdownMenuItem("GitHub", href="https://github.com/HYLODE"),
            ],
            nav=True,
            in_navbar=True,
            label="Dev",
        ),
    ],
    brand="HYLODE",
    brand_href="#",
    sticky="top",
    class_name="mb-2",
)

app.layout = dbc.Container(
    [
        navbar,
        page_container,
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
