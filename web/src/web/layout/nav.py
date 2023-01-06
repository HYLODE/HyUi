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
sitrep = _NavLink(title="SitRep", path="/sitrep", icon="carbon:location-current")


def create_side_navbar() -> dmc.Navbar:
    return dmc.Navbar(
        fixed=True,
        id="components-navbar",
        position={"top": 70},
        width={"base": 150},
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
            create_main_nav_link(
                icon=sitrep.icon,
                label=sitrep.title,
                href=sitrep.path,
            ),
        ],
    )

    return dmc.Stack(spacing="sm", children=[main_links, dmc.Space(h=20)], px=25)


def create_main_nav_link(icon: str, label: str, href: str) -> dmc.Anchor:
    return dmc.Anchor(
        dmc.Group(
            [
                DashIconify(
                    icon=icon, width=23, color=dmc.theme.DEFAULT_COLORS["indigo"][5]
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
        size=150,
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
