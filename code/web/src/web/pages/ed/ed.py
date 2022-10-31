from dash import register_page, html, dcc
from flask_login import current_user

register_page(__name__, name="ED Admissions")


def layout():
    if not current_user.is_authenticated:
        return html.Div(["Please ", dcc.Link("login", href="/login"), " to continue"])
    return html.Div("ED Placeholder")
