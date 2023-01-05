import dash_bootstrap_components as dbc
import os
from dash import page_registry
from typing import NamedTuple


class NavbarDropdown(NamedTuple):
    label: str
    url: str
    header: bool


CORE_PAGES = ["SITREP", "PACU", "PERRT", "ED"]
ADMIN_PAGES = ["Home", "Login", "Logout"]
HIDDEN_PAGES: list[str] = [
    "Sitlist",
    "Beds",
    "Census",
    "Consults",
    "Demo",
    "HyMind",
]

dropdown_more = [
    NavbarDropdown("Additional reports", "", header=True),
    NavbarDropdown("COVID SitRep", "http://172.16.149.205:5701/sitrep/T03", False),
]
dropdown_dev = [
    NavbarDropdown("Developer Tools", "", True),
    NavbarDropdown("Beta version", "https://172.16.149.202:8300/", False),
    NavbarDropdown("GitHub", "https://github.com/HYLODE", False),
    NavbarDropdown("Configuration", os.getenv("BASEROW_PUBLIC_URL", ""), False),
    # NavbarDropdown("HYLODE", "http://172.16.149.202:5001/", False),
    # NavbarDropdown("HYMIND Lab", "http://172.16.149.202:5009/", False),
    # NavbarDropdown("HYUI API", "http://172.16.149.202:6002/docs", False),
]


def header_pages_dropdown():
    """Filters and sorts pages from registry for display in main navbar"""
    pp = {page["name"].upper(): page["path"] for page in page_registry.values()}

    return [
        dbc.NavItem(dbc.NavLink(page, href=pp[page.upper()])) for page in CORE_PAGES
    ]


def more_list():
    """
    Filters and sorts pages from registry for dropdown
    Part 1 = extra apps
    Part 2 = dev apps
    """
    pp = []
    for page in dropdown_more:
        pp.append(dbc.DropdownMenuItem(page.label, href=page.url, header=page.header))
    for page in page_registry.values():
        exclude_pages = [i.title() for i in CORE_PAGES]
        exclude_pages = exclude_pages + ADMIN_PAGES + HIDDEN_PAGES
        exclude_pages = [i.lower() for i in exclude_pages]
        if page["name"].lower() in exclude_pages:
            continue
        pp.append(dbc.DropdownMenuItem(page["name"], href=page["path"]))
    for page in dropdown_dev:
        pp.append(dbc.DropdownMenuItem(page.label, href=page.url, header=page.header))

    return pp


navbar = dbc.NavbarSimple(
    children=[
        dbc.Nav(children=header_pages_dropdown()),
        dbc.DropdownMenu(
            children=more_list(),
            nav=True,
            in_navbar=True,
            label="MORE",
        ),
        dbc.NavItem(id="login-status"),
    ],
    brand="HYLODE",
    brand_href="/",
    sticky="top",
    class_name="mb-1 p-0",
    color="primary",
    dark=True,
)
