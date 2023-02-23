import dash

from dash import html


dash.register_page(__name__, path="/surgery/pqip", name="PQIP Reporting Dashboard")

pqip = html.Iframe(
    src="/assets/pqip_dashboard.html",
    style={"height": "1000px", "width": "100%"},
)


def layout() -> dash.html.Div:
    return html.Div(children=[pqip])
