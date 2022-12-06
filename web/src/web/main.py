import tempfile
from typing import NamedTuple

import dash_bootstrap_components as dbc
from dash import (
    Dash,
    Input,
    Output,
    State,
    dcc,
    html,
    page_container,
    page_registry,
    DiskcacheManager,
)
from flask import Flask
from flask_login import LoginManager, UserMixin, current_user, login_user

from web.config import get_settings

import diskcache


class NavbarDropdown(NamedTuple):
    label: str
    url: str
    header: bool


BPID = "app_"
CORE_PAGES = ["Sitrep", "Electives", "PERRT", "ED"]
ADMIN_PAGES = ["Home", "Login", "Logout"]
HIDDEN_PAGES: list[str] = []

dropdown_more = [
    NavbarDropdown("Additional reports", "", header=True),
    NavbarDropdown("COVID SitRep", "http://uclvlddpragae08:5701/sitrep/T03", False),
]
dropdown_dev = [
    NavbarDropdown("Developer Tools", "", True),
    NavbarDropdown("GitHub", "https://github.com/HYLODE", False),
    NavbarDropdown("HYLODE", "http://172.16.149.202:5001/", False),
    NavbarDropdown("HYMIND Lab", "http://172.16.149.202:5009/", False),
    NavbarDropdown("HYUI API", "http://172.16.149.202:8094/docs", False),
    NavbarDropdown("BaseRow", "http://172.16.149.202:8097", False),
    NavbarDropdown("PGWeb", "http://172.16.149.202:8099", False),
]

# Exposing the Flask Server to enable configuring it for logging in
# https://github.com/AnnMarieW/dash-flask-login
server = Flask(__name__)

cache = diskcache.Cache(tempfile.TemporaryDirectory().name)

app = Dash(
    __name__,
    server=server,
    title="HYLODE",
    update_title=None,
    external_stylesheets=[
        dbc.themes.LUX,
        dbc.icons.FONT_AWESOME,
    ],
    suppress_callback_exceptions=True,
    use_pages=True,
    background_callback_manager=DiskcacheManager(cache),
)

# Updating the Flask Server configuration with Secret Key to encrypt the user
# session cookie.
server.config.update(SECRET_KEY=get_settings().secret_key.get_secret_value())

# Login manager object will be used to login / logout users
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"


class User(UserMixin):
    # User data model. It has to have at least self.id as a minimum
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(username):
    """
    This function loads the user by user id. Typically, this looks up the
    user from a user database. We won't be registering or looking up users in
    this example, since we'll just login using LDAP server. So we'll simply
    return a User object with the passed in username.
    """
    return User(username)


@app.callback(
    Output("login-status", "children"),
    Input("url-for-app", "pathname"),
)
def update_authentication_status(_):
    if current_user.is_authenticated:
        return dbc.NavLink("logout", href="/logout")
    return dbc.NavLink("login", href="/login")


@app.callback(
    Output("hidden_div_for_login_button_output", "children"),  # html.div on login.py
    Input("login-button", "n_clicks"),
    State("uname-box", "value"),
    State("pwd-box", "value"),
    prevent_initial_call=True,
)
def login_button_click(
    n_clicks: int, username: str, password: str
) -> dcc.Location | str:
    if n_clicks <= 0:
        return ""

    settings = get_settings()

    if (
        settings.username != username
        or settings.password.get_secret_value() != password
    ):
        return "Invalid username or password"

    login_user(User(username))
    return dcc.Location(pathname="/", id="not_in_use_01")


def header_pages_dropdown():
    """Filters and sorts pages from registry for display in main navbar"""
    pp = {page["name"]: page["path"] for page in page_registry.values()}

    return [
        dbc.NavItem(dbc.NavLink(page, href=pp[page.title()])) for page in CORE_PAGES
    ]


def more_list():
    """
    Filters and sorts pages from registry for dropdown
    Part 1 = extra apps
    Part 2 = dev apps
    """
    pp = []
    for page in dropdown_more:
        pp.append(dbc.DropdownMenuItem(page.label, href=page.url, header=page.header))
    for page in page_registry.values():
        exclude_pages = [i.title() for i in CORE_PAGES]
        exclude_pages = exclude_pages + ADMIN_PAGES + HIDDEN_PAGES
        if page["name"] in exclude_pages:
            continue
        pp.append(dbc.DropdownMenuItem(page["name"], href=page["path"]))
    for page in dropdown_dev:
        pp.append(dbc.DropdownMenuItem(page.label, href=page.url, header=page.header))

    return pp


navbar = dbc.NavbarSimple(
    children=[
        dbc.Nav(children=header_pages_dropdown()),
        dbc.DropdownMenu(
            children=more_list(),
            nav=True,
            in_navbar=True,
            label="More",
        ),
        dbc.NavItem(id="login-status"),
    ],
    brand="HYLODE",
    brand_href="/",
    sticky="top",
    class_name="mb-2",
)

dash_only = html.Div(
    [
        html.Div(id="hidden_div_for_login_callback"),
        dcc.Location(id="url-for-app"),
    ]
)

app.layout = dbc.Container(
    [
        navbar,
        page_container,
        dash_only,
    ],
    fluid=True,
    className="dbc",
)


# standalone apps : please use ports fastapi 8200 and dash 8201
# this is the callable object run by gunicorn
# cd ./src/
# gunicorn -w 4 --bind 0.0.0.0:8093 apps.app:server
server = app.server


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=get_settings().development_port, debug=True)