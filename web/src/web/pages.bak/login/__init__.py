import dash_bootstrap_components as dbc
from dash import html

not_logged_in_div_content = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    html.Div(
                        [
                            html.H2("Welcome", className="text-center"),
                            dbc.NavLink(
                                html.H6("Please log in", className="text-center"),
                                href="/login/login",
                            ),
                        ],
                        className="position-absolute translate-middle top-50 start-50",
                    )
                ],
                className="m-3",
                width=4,
            ),
        ],
        className="g-2 p-5 position-absolute translate-middle top-50 start-50",
        justify="center",
    )
)
