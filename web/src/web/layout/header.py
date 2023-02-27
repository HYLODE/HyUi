import dash_mantine_components as dmc
from dash import Input, Output, State, clientside_callback
from dash_iconify import DashIconify
from web.config import get_settings

settings = get_settings()


def create_home_link(label: str) -> dmc.Anchor:
    return dmc.Anchor(
        label,
        size="xl",
        href="/",
        underline=False,
    )


def create_header_link(
    icon: str, href: str, size: int = 22, color: str = "indigo"
) -> dmc.Anchor:
    return dmc.Anchor(
        dmc.ThemeIcon(
            DashIconify(
                icon=icon,
                width=size,
            ),
            variant="outline",
            radius=30,
            size=36,
            color=color,
        ),
        href=href,
        target="_blank",
    )


def create_header(nav_data: list | dict) -> dmc.Header:
    # NOTE: extract first item if nav_data is returned as a nested list
    # template copied from https://github.com/snehilvj/dmc-docs/
    # but there are no nested pages
    try:
        next(iter(nav_data))["name"]
    except TypeError:
        nav_data = nav_data[0]
    finally:
        _select_list = [
            {
                "label": component["name"],
                "value": component["path"],
            }
            for component in nav_data
            if component["name"] not in ["Home", "Not found 404"]
        ]

    return dmc.Header(
        height=70,
        fixed=True,
        px=25,
        children=[
            dmc.Stack(
                justify="center",
                style={"height": 70},
                children=dmc.Grid(
                    children=[
                        dmc.Col(
                            [
                                dmc.MediaQuery(
                                    create_home_link("HyperLocal Demand " "Forecasts"),
                                    smallerThan=1500,
                                    styles={"display": "none"},
                                ),
                                dmc.MediaQuery(
                                    create_home_link("HYLODE"),
                                    largerThan=1500,
                                    styles={"display": "none"},
                                ),
                            ],
                            span="content",
                            pt=12,
                        ),
                        # Create a search box and pre-populate with page names
                        dmc.Col(
                            span="auto",
                            children=dmc.Group(
                                position="right",
                                spacing="xl",
                                children=[
                                    dmc.MediaQuery(
                                        dmc.Select(
                                            id="select-component",
                                            style={"width": 250},
                                            placeholder="Search",
                                            nothingFound="No match found",
                                            searchable=True,
                                            clearable=True,
                                            data=_select_list,
                                            icon=DashIconify(
                                                icon="radix-icons:magnifying-glass"
                                            ),
                                        ),
                                        smallerThan=1200,
                                        styles={"display": "none"},
                                    ),
                                    create_header_link(
                                        "radix-icons:github-logo",
                                        "https://github.com/hylode/hyui",
                                    ),
                                    create_header_link(
                                        "carbon:help", "https://hylode.org"
                                    ),
                                    create_header_link(
                                        "carbon:settings", settings.baserow_public_url
                                    ),
                                    dmc.ActionIcon(
                                        DashIconify(
                                            icon="radix-icons:blending-mode", width=22
                                        ),
                                        variant="outline",
                                        radius=30,
                                        size=36,
                                        color="yellow",
                                        id="color-scheme-toggle",
                                    ),
                                    dmc.MediaQuery(
                                        dmc.ActionIcon(
                                            DashIconify(
                                                icon="radix-icons:hamburger-menu",
                                                width=18,
                                            ),
                                            id="drawer-hamburger-button",
                                            variant="outline",
                                            size=36,
                                        ),
                                        largerThan=1500,
                                        styles={"display": "none"},
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            )
        ],
    )


clientside_callback(
    """ function(data) { return data } """,
    Output("mantine-docs-theme-provider", "theme"),
    Input("theme-store", "data"),
)

clientside_callback(
    """function(n_clicks, data) {
        if (data) {
            if (n_clicks) {
                const scheme = data["colorScheme"] == "dark" ? "light" : "dark"
                return { colorScheme: scheme }
            }
            return dash_clientside.no_update
        } else {
            return { colorScheme: "light" }
        }
    }""",
    Output("theme-store", "data"),
    Input("color-scheme-toggle", "n_clicks"),
    State("theme-store", "data"),
)

# noinspection PyProtectedMember
clientside_callback(
    """ function(children) { return null } """,
    Output("select-component", "value"),
    Input("_pages_content", "children"),
)

clientside_callback(
    """
    function(value) {
        if (value) {
            return value
        }
    }
    """,
    Output("url", "pathname"),
    Input("select-component", "value"),
)

clientside_callback(
    """function(n_clicks) { return true }""",
    Output("components-navbar-drawer", "opened"),
    Input("drawer-hamburger-button", "n_clicks"),
    prevent_initial_call=True,
)
