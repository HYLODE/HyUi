# src/utils/__init__.py

from importlib import import_module
from config.settings import settings  # type: ignore


def gen_module_path(name: str, root: str = settings.MODULE_ROOT) -> str:
    """
    Concatenates strings into a module path
    e.g. 'api' and 'consults' becomes 'api.consults'
    """
    return f"{root}.{name}"


def get_model_from_route(route: str, subclass: str = None):
    route_title_case = route.title()
    if subclass:
        subclass = subclass.title()
        route_title_case = f"{route_title_case}{subclass}"
    route_path = gen_module_path(route.lower())
    model = getattr(import_module(route_path), route_title_case)  # noqa
    return model
