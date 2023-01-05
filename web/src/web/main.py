"""
Principal landing page for the Plotly Dash application
"""
import dash_bootstrap_components as dbc
import diskcache
import tempfile
from dash import (
    Dash,
    DiskcacheManager,
    Input,
    Output,
    State,
    dcc,
    html,
    page_container,
)
from flask import Flask
from flask_login import LoginManager, UserMixin, current_user, login_user
from uuid import uuid4

from web.config import get_settings

# TODO: ask @harry if we need this once the Varnish cache works
launch_uuid = uuid4()
cache = diskcache.Cache(tempfile.TemporaryDirectory().name)
background_callback_manager = DiskcacheManager(
    cache, cache_by=[lambda: launch_uuid], expire=600  # seconds
)

# Exposing the Flask Server to enable configuring it for logging in
# https://github.com/AnnMarieW/dash-flask-login
server = Flask(__name__)

app = Dash(
    __name__,
    server=server,
    title="HYLODE",
    update_title=None,
    external_stylesheets=[
        dbc.themes.COSMO,
        dbc.icons.FONT_AWESOME,
    ],
    suppress_callback_exceptions=True,
    use_pages=True,
    background_callback_manager=background_callback_manager,
)

# need to build the app to allow page registry to be initialised before this
# import
from web.nav import navbar

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
    """
    Toggles the Login/Logout link on the menu bar
    """
    if current_user.is_authenticated:
        return dbc.NavLink("LOG OUT", href="/login/logout")
    return dbc.NavLink("LOG IN", href="/login/login")


@app.callback(
    Output("hidden_div_for_login_button_output", "children"),
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


dash_only = html.Div(
    [
        html.Div(id="hidden_div_for_login_callback"),
        dcc.Location(id="url-for-app"),
    ]
)

footer = html.Div(
    [
        html.P(
            "Built for the NHS | Made at UCLH | Funded by NHS-X and NIHR",
            className="position-absolute translate-middle top-100 start-50",
        )
    ]
)

app.layout = dbc.Container(
    [
        navbar,
        page_container,
        dash_only,
        # footer,
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
