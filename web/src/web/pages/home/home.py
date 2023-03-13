import dash
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

# noqa suppresses black errors when linting since you need this import for
# access to callbacks
import web.pages.sitrep.callbacks.cytoscape  # noqa
from web.style import colors

dash.register_page(__name__, path="/", name="Home")

timers = html.Div([])
stores = html.Div([])

_inline = {"display": "inline"}

body = html.Div(
    [
        dmc.Paper(
            children=[
                dmc.Title(
                    children=[
                        "Welcome ",
                        DashIconify(icon="mdi:greeting-outline", inline=True),
                    ],
                    color=colors.indigo,
                ),
                dmc.Divider(),
                dmc.Grid(
                    [
                        dmc.Col(
                            [
                                dmc.Paper(
                                    children=dmc.Title(
                                        children="User notes",
                                        order=2,
                                        color=colors.gray,
                                    ),
                                    shadow="lg",
                                    radius="lg",
                                    p="lg",
                                ),
                                dmc.Paper(
                                    [
                                        dmc.List(
                                            [
                                                dmc.ListItem(
                                                    dmc.Text(
                                                        [
                                                            "The application is in ",
                                                            dmc.Text(
                                                                "beta ",
                                                                color=colors.orange,
                                                                style=_inline,
                                                            ),
                                                            "please be careful ",
                                                            "but please also let us "
                                                            "know what "
                                                            "you think",
                                                        ]
                                                    )
                                                ),
                                                dmc.ListItem(
                                                    dmc.Text(
                                                        [
                                                            DashIconify(
                                                                icon="carbon:tool-kit",
                                                                inline=True,
                                                                color=colors.red,
                                                            ),
                                                            " It's taking a while for the app "
                                                            "to load up all the data at the "
                                                            "start of the day. Sorry. We're "
                                                            "working on a fix but thanks for "
                                                            "being patient for now",
                                                        ]
                                                    )
                                                ),
                                                dmc.ListItem(
                                                    [
                                                        "Please report bugs ",
                                                        DashIconify(
                                                            icon="carbon:debug",
                                                            inline=True,
                                                            color=colors.red,
                                                        ),
                                                        " and issues via ",
                                                        dmc.Anchor(
                                                            "email",
                                                            href="mailto:s.harris8@nhs.net",
                                                            inline=True,
                                                        ),
                                                        " or directly on ",
                                                        dmc.Anchor(
                                                            "GitHub",
                                                            href="https://github.com/hylode/hyui",
                                                            inline=True,
                                                        ),
                                                    ]
                                                ),
                                            ],
                                            size="md",
                                            spacing="sm",
                                            withPadding=False,
                                        ),
                                    ],
                                    shadow="lg",
                                    radius="lg",
                                    p="lg",
                                ),
                            ],
                            span=4,
                        ),
                        dmc.Col(
                            [
                                dmc.Paper(
                                    children=dmc.Title(
                                        children="Quick-start guide to the ward maps",
                                        order=2,
                                        color=colors.gray,
                                    ),
                                    shadow="lg",
                                    radius="lg",
                                    p="lg",
                                ),
                                dmc.Paper(
                                    children=dmc.Image(
                                        src="/assets/cytoscape.drawio.png",
                                        alt="Legend for ward maps",
                                        width="100%",
                                    ),
                                    shadow="lg",
                                    radius="lg",
                                    p="lg",
                                ),
                            ],
                            span=8,
                        ),
                    ]
                )
                #     TODO: insert project timeline
            ],
            shadow="lg",
            radius="lg",
            p="md",  # padding
            withBorder=True,
        ),
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
