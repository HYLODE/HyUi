import dash_mantine_components as dmc
from dash_iconify import DashIconify
from typing import NamedTuple

navbar_icons = {
    "Data Display": "radix-icons:dashboard",
    "Inputs": "radix-icons:input",
    "Feedback": "radix-icons:info-circled",
    "Overlay": "radix-icons:stack",
    "Navigation": "radix-icons:hamburger-menu",
    "Typography": "radix-icons:letter-case-capitalize",
    "Layout": "radix-icons:container",
    "Miscellaneous": "radix-icons:mix",
    "Buttons": "radix-icons:button",
}


class _NavLink(NamedTuple):
    title: str
    path: str
    icon: str


home = _NavLink(title="Home", path="/", icon="carbon:home")
scratch = _NavLink(title="Scratch", path="/demo", icon="ph:number-square-three-light")

sitrep_campus = _NavLink(title="Campus", path="/sitrep/campus", icon="carbon:hospital")
# sitrep_ward = _NavLink(title="Ward", path="/sitrep/ward", icon="carbon:hospital-bed")
electives = _NavLink(
    title="Electives", path="/surgery/electives", icon="carbon:calendar"
)
pqip = _NavLink(
    title="PQIP Report", path="/assets/pqip_dashboard.html", icon="mdi:graph-areaspline"
)
a_and_e = _NavLink(
    title="Admissions", path="/a_and_e", icon="fluent:people-queue-24-regular"
)
sitrep_icus = _NavLink(
    title="Critical Care", path="/sitrep/icus", icon="healthicons:critical-care-outline"
)
perrt = _NavLink(title="PERRT", path="/sitrep/perrt", icon="carbon:stethoscope")

ed_predictor = _NavLink(
    title="ED Predictor", path="/ed/table", icon="carbon:machine-learning-model"
)


def create_side_navbar() -> dmc.Navbar:
    return dmc.Navbar(
        fixed=True,
        id="components-navbar",
        position={"top": 70},
        width={"base": 250},
        children=[
            dmc.ScrollArea(
                offsetScrollbars=True,
                type="scroll",
                children=create_side_nave_content(),
            )
        ],
    )


def create_side_nave_content() -> dmc.Stack:
    main_links = dmc.Stack(
        spacing="sm",
        mt=20,
        children=[
            create_main_nav_link(
                icon=home.icon,
                label=home.title,
                href=home.path,
            ),
            dmc.Divider(
                labelPosition="left",
                label=[
                    DashIconify(
                        icon="carbon:location-current",
                        width=20,
                        style={"marginRight": 10},
                        color=dmc.theme.DEFAULT_COLORS["indigo"][5],
                    ),
                    "Sitrep",
                ],
                my=20,
            ),
            create_main_nav_link(
                icon=sitrep_icus.icon,
                label=sitrep_icus.title,
                href=sitrep_icus.path,
            ),
            create_main_nav_link(
                icon=sitrep_campus.icon,
                label=sitrep_campus.title,
                href=sitrep_campus.path,
            ),
            # create_main_nav_link(
            #     icon=sitrep_ward.icon,
            #     label=sitrep_ward.title,
            #     href=sitrep_ward.path,
            # ),
            dmc.Divider(
                labelPosition="left",
                label=[
                    DashIconify(
                        icon="carbon:scalpel",
                        width=20,
                        style={"marginRight": 10},
                        color=dmc.theme.DEFAULT_COLORS["indigo"][5],
                    ),
                    "Surgery",
                ],
                my=20,
            ),
            create_main_nav_link(
                icon=electives.icon,
                label=electives.title,
                href=electives.path,
            ),
            dmc.Anchor(
                dmc.Group(
                    [
                        DashIconify(
                            icon=pqip.icon,
                            width=20,
                            color=dmc.theme.DEFAULT_COLORS["indigo"][5],
                        ),
                        dmc.Text(pqip.title, size="sm"),
                    ]
                ),
                href=pqip.path,
                variant="text",
                target="_blank",
            ),
            dmc.Divider(
                labelPosition="left",
                label=[
                    DashIconify(
                        icon="healthicons:ambulance-outline",
                        width=20,
                        style={"marginRight": 10},
                        color=dmc.theme.DEFAULT_COLORS["indigo"][5],
                    ),
                    "Emergencies",
                ],
                my=20,
            ),
            create_main_nav_link(
                icon=perrt.icon,
                label=perrt.title,
                href=perrt.path,
            ),
            create_main_nav_link(
                icon=ed_predictor.icon,
                label=ed_predictor.title,
                href=ed_predictor.path,
            ),
            dmc.Divider(
                labelPosition="left",
                label=[
                    DashIconify(
                        icon="carbon:code",
                        width=20,
                        style={"marginRight": 10},
                        color=dmc.theme.DEFAULT_COLORS["indigo"][5],
                    ),
                    "Development",
                ],
                my=20,
            ),
            create_main_nav_link(
                icon=scratch.icon,
                label=scratch.title,
                href=scratch.path,
            ),
        ],
    )

    return dmc.Stack(spacing="sm", children=[main_links, dmc.Space(h=20)], px=25)


def create_main_nav_link(icon: str, label: str, href: str) -> dmc.Anchor:
    return dmc.Anchor(
        dmc.Group(
            [
                DashIconify(
                    icon=icon, width=20, color=dmc.theme.DEFAULT_COLORS["indigo"][5]
                ),
                dmc.Text(label, size="sm"),
            ]
        ),
        href=href,
        variant="text",
    )


def create_navbar_drawer() -> dmc.Drawer:
    return dmc.Drawer(
        id="components-navbar-drawer",
        overlayOpacity=0.55,
        overlayBlur=3,
        zIndex=9,
        size=250,
        children=[
            dmc.ScrollArea(
                offsetScrollbars=True,
                type="scroll",
                style={"height": "100%"},
                pt=20,
                children=create_side_nave_content(),
            )
        ],
    )
