# src/utils/__init__.py

from config.settings import settings


def gen_module_path(name: str, root: str = settings.MODULE_ROOT) -> str:
    return f"{root}.{name}"
