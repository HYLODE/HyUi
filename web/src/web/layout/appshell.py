import dash_mantine_components as dmc
from dash import dcc, html, page_container

from web.layout.header import create_header
from web.layout.nav import create_navbar_drawer, create_side_navbar


def create_appshell(nav_data: list | dict) -> dmc.MantineProvider:
    return dmc.MantineProvider(
        dmc.MantineProvider(
            theme={
                "fontFamily": "'Inter', sans-serif",
                "primaryColor": "indigo",
                "components": {
                    "Button": {"styles": {"root": {"fontWeight": 400}}},
                    "Alert": {"styles": {"title": {"fontWeight": 500}}},
                    "AvatarGroup": {"styles": {"truncated": {"fontWeight": 500}}},
                },
            },
            inherit=True,
            children=[
                dcc.Store(id="theme-store", storage_type="local"),
                dcc.Location(id="url"),
                dmc.NotificationsProvider(
                    [
                        create_header(nav_data),
                        create_side_navbar(),
                        create_navbar_drawer(),
                        html.Div(
                            dmc.Container(size="lg", pt=90, children=page_container),
                            id="wrapper",
                        ),
                    ]
                ),
            ],
        ),
        theme={"colorScheme": "light"},
        id="mantine-docs-theme-provider",
        withGlobalStyles=True,
        withNormalizeCSS=True,
    )
