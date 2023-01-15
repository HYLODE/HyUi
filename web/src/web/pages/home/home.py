import dash
import dash_mantine_components as dmc
from dash import html

# noqa suppresses black errors when linting since you need this import for
# access to callbacks
import web.pages.sitrep.callbacks  # noqa
from web.style import colors

dash.register_page(__name__, path="/", name="Home")

timers = html.Div([])
stores = html.Div([])

body = html.Div(
    [
        dmc.Paper(
            [
                dmc.Text(
                    dmc.Title(
                        "👋Welcome! ",
                    ),
                    color=colors.indigo,
                ),
                dmc.Divider(),
                dmc.Container(
                    [
                        dmc.List(
                            [
                                dmc.ListItem(
                                    dmc.Text(
                                        [
                                            "🚧The application is in alpha ",
                                            "please be careful",
                                            "but please also let us know what you think",
                                        ]
                                    )
                                ),
                                dmc.ListItem(
                                    "🍔 Use the burger menu (top right) or the "
                                    "side bar to navigate"
                                ),
                                dmc.ListItem(
                                    "🐛Please report bugs and issues on our "
                                    "slack channel "
                                    "or directly on github "
                                ),
                            ],
                            size="md",
                            spacing="sm",
                            withPadding=False,
                        ),
                    ],
                    pt="md",
                ),
                #     TODO: insert project timeline
            ],
            shadow="lg",
            radius="lg",
            p="md",  # padding
            withBorder=True,
        )
    ]
)


def layout() -> dash.html.Div:
    return html.Div(
        children=[
            timers,
            stores,
            body,
        ]
    )
