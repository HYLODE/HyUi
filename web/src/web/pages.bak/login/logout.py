import dash
import dash_bootstrap_components as dbc
from dash import html
from flask_login import current_user, logout_user

dash.register_page(__name__)

logged_out = html.Div(
    dbc.Row(
        [
            dbc.Col(
                html.H2("Bye!"),
                className="me-3",
                width=2,
            ),
        ],
        className="g-2 p-5 position-absolute translate-middle top-50 start-50",
        justify="center",
    )
)


def layout():
    if current_user.is_authenticated:
        logout_user()
    return logged_out
