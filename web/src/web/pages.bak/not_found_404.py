import dash_bootstrap_components as dbc
from dash import html, register_page


layout = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    html.Div(
                        [
                            html.H2("Sorry!", className="text-center"),
                            html.H6(
                                "We couldn't find that page", className="text-center"
                            ),
                            dbc.NavLink(
                                html.H6("Return home", className="text-center"),
                                href="/home",
                            ),
                        ],
                        className="position-absolute translate-middle top-50 start-50",
                    )
                ],
                className="m-3",
                width=4,
            ),
        ],
        className="g-2 p-5",
        justify="center",
    )
)

register_page(__name__, layout=layout)
