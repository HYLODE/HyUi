# src/apps/app.py
"""
The application itself
"""
import dash
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, dcc, html, page_container, page_registry
from flask import Flask
from flask_login import login_user, LoginManager, UserMixin, current_user

from config.settings import settings

BPID = "app_"
CORE_PAGES = ["Sitrep", "Electives", "PERRT"]
ED_PAGE_URL = "http://uclvlddpragae08:5212/"

# Exposing the Flask Server to enable configuring it for logging in
# https://github.com/AnnMarieW/dash-flask-login
server = Flask(__name__)
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
)

# Keep this out of source code repository - save in a file or a database
#  passwords should be encrypted
VALID_USERNAME_PASSWORD = {"test": "test", "hello": "world"}


# Updating the Flask Server configuration with Secret Key to encrypt the user session cookie
server.config.update(SECRET_KEY=settings.SECRET_KEY)

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
    """This function loads the user by user id. Typically this looks up the user from a user database.
    We won't be registering or looking up users in this example, since we'll just login using LDAP server.
    So we'll simply return a User object with the passed in username.
    """
    return User(username)


@app.callback(
    Output("user-status-header", "children"),
    Input("url", "pathname"),
)
def update_authentication_status(_):
    if current_user.is_authenticated:
        return dcc.Link("logout", href="/logout")
    return dcc.Link("login", href="/login")


@app.callback(
    Output("output-state", "children"),
    Input("login-button", "n_clicks"),
    State("uname-box", "value"),
    State("pwd-box", "value"),
    prevent_initial_call=True,
)
def login_button_click(n_clicks, username, password):
    if n_clicks > 0:
        if VALID_USERNAME_PASSWORD.get(username) is None:
            return "Invalid username"
        if VALID_USERNAME_PASSWORD.get(username) == password:
            login_user(User(username))
            return "Login Successful"
        return "Incorrect  password"


def header_pages_dropdown():
    """Filters and sorts pages from registry for display in main navbar"""
    pp = {page["name"]: page["path"] for page in page_registry.values()}

    ll = [dbc.NavItem(dbc.NavLink(page, href=pp[page.title()])) for page in CORE_PAGES]

    # ED page placeholder
    ll.append(dbc.NavItem(dbc.NavLink("ED", href=ED_PAGE_URL, target="_blank")))

    return ll


def extra_apps():
    """Filters and sorts pages from registry for dropdown"""
    pp = []
    for page in page_registry.values():
        Core_Pages = [i.title() for i in CORE_PAGES]
        if page["name"] in Core_Pages or page["name"] == "Home":
            continue
        pp.append(dbc.DropdownMenuItem(page["name"], href=page["path"]))
    return pp


# TODO: tidy up this mess!
more_list = [
    dbc.DropdownMenuItem("Additional reports", header=True),
    dbc.DropdownMenuItem("COVID SitRep", href="http://uclvlddpragae08:5701/sitrep/T03"),
]
more_list = more_list + extra_apps()
dev_list = [
    dbc.DropdownMenuItem("Developer Tools", header=True),
    dbc.DropdownMenuItem("GitHub", href="https://github.com/HYLODE"),
    dbc.DropdownMenuItem("HYLODE", href="http://172.16.149.202:5001/"),
    dbc.DropdownMenuItem("HYMIND Lab", href="http://172.16.149.202:5009/"),
    dbc.DropdownMenuItem("HYUI API", href="http://172.16.149.202:8094/docs"),
    dbc.DropdownMenuItem("BaseRow", href="http://172.16.149.202:8097"),
    dbc.DropdownMenuItem("PGWeb", href="http://172.16.149.202:8099"),
]
more_list = more_list + dev_list


navbar = dbc.NavbarSimple(
    children=[
        dbc.Nav(children=header_pages_dropdown()),
        dbc.DropdownMenu(
            children=more_list,
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand="HYLODE",
    brand_href="/",
    sticky="top",
    class_name="mb-2",
)

app.layout = dbc.Container(
    [
        dcc.Location(id="url"),
        html.Div(id="user-status-header"),
        html.Hr(),
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
