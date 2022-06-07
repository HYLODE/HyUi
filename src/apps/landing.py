"""
Menu and landing page
"""
from dash import dcc, html
import dash_bootstrap_components as dbc

from app import app


REFRESH_INTERVAL = 5 * 60 * 1000  # milliseconds

landing_notes = dcc.Markdown(
"""
### Welcome to the UCLH critical care sitrep and bed management tool

Here's what we're working on!

"""
)

header = dbc.Container(
    dbc.Row(
        [
            # dbc.Col([
            #             html.I(className="fa fa-lungs-virus"),
            #             ], md=1),
            dbc.Col(
                [
                    dbc.NavbarSimple(
                        children=[
                            dbc.NavItem(dbc.NavLink("CONSULTS", href="/consults")),
                        ],
                        brand="UCLH Critical Care Sitrep",
                        brand_href="/",
                        brand_external_link=True,
                        color="primary",
                        dark=True,
                        sticky=True,
                    ),
                ]
            ),
        ]
    ),
    fluid=True,
)


main = dbc.Container(
    [
        # All content here organised as per bootstrap
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H6("HyperLocal Bed Demand Forecasts")),
                        dbc.CardBody(html.Div([landing_notes])),
                    ],
                ),
                md=12,
            ),
        ),
        # dbc.Row([
        #     html.Img(src=app.get_asset_url('hylode-project-plan.png'))
        #     ]),
    ],
    fluid=True,
)

# use this to store dash components that you don't need to 'see'
# dash_stores = html.Div(
#     [
#         # update and refresh
#         dcc.Interval(
#             id="landing-interval-data", interval=REFRESH_INTERVAL, n_intervals=0
#         ),
#         # use this to source-data
#         dcc.Store(id="landing-source-data"),
#     ]
# )

# """Principal layout for landing page"""
landing = dbc.Container(
    fluid=True,
    className="dbc",
    children=[
        header,
        main,
        # dash_stores,
    ],
)


