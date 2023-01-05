import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__)


form = dbc.Form(
    dbc.Row(
        [
            dbc.Label("Username", width="auto"),
            dbc.Col(
                dbc.Input(
                    type="text",
                    placeholder="Enter username",
                    id="uname-box",
                ),
                className="me-3",
                width=3,
            ),
            dbc.Label("Password", width="auto"),
            dbc.Col(
                dbc.Input(
                    type="password",
                    placeholder="Enter password",
                    id="pwd-box",
                ),
                className="me-3",
                width=3,
            ),
            dbc.Col(
                dbc.Button(
                    "Submit",
                    color="primary",
                    n_clicks=0,
                    id="login-button",
                    type="submit",
                ),
                width="auto",
            ),
        ],
        className="g-2 p-5 position-absolute translate-middle top-50 start-50",
        justify="center",
    )
)
# Login screen
layout = html.Div(
    [
        form,
        html.Div(children="", id="hidden_div_for_login_button_output"),
    ]
)
