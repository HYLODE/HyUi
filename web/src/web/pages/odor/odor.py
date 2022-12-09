from dash import html, register_page, dcc

from flask_login import current_user

register_page(__name__)


def layout():
    if not current_user.is_authenticated:
        return html.Div(["Please ", dcc.Link("login", href="/login"), " to continue"])
    return html.Div(
        [
            main,
        ],
    )


main = html.Iframe(
    src="/assets/odor_dashboard.html",
    style={"height": "1000px", "width": "100%"},
)
