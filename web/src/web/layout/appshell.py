import dash_mantine_components as dmc
from dash import dcc, html, page_container

from web.layout.header import create_header
from web.layout.nav import create_navbar_drawer, create_side_navbar
from web import ids
from web.stores import stores


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
                dcc.Interval(
                    id=ids.STORE_TIMER_1H,
                    n_intervals=0,
                    interval=60 * 60 * 1000,
                ),
                dcc.Interval(
                    id=ids.STORE_TIMER_6H,
                    n_intervals=0,
                    interval=6 * 60 * 60 * 1000,
                ),
                stores,
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
