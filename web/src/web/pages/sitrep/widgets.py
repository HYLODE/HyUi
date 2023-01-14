import dash_mantine_components as dmc


def page_status_controls(status: list[dmc.Col], controls: list[dmc.Col]) -> dmc.Paper:
    """Function to define consistent layout to status and controls across
    pages"""
    return dmc.Paper(
        [
            dmc.Grid(
                [
                    dmc.Center(style={"width": "100%"}, children=[*controls]),
                    *status,
                ],
                grow=False,
                gutter="m",
            )
        ],
        p="xs",
    )


def tab_status_controls(status: list[dmc.Col], controls: list[dmc.Col]) -> dmc.Paper:
    """Function to define consistent layout to status and controls across
    tabs"""
    return dmc.Paper(
        [
            dmc.Grid(
                [
                    *controls,
                    *status,
                ],
                grow=False,
                gutter="m",
            )
        ],
        p="xs",
    )
