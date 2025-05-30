import importlib
import inspect
import pkgutil
from typing import Iterator, NoReturn

from bot import extensions

def walk_extensions() -> Iterator[str]:
    """
    Automatically walk through all the Cogs in the extensions folder and add
    them to a list for easy setup
    """

    def on_error(name: str) -> NoReturn:
        raise ImportError(name=name)

    for module in pkgutil.walk_packages(
        extensions.__path__, f"{extensions.__name__}.", onerror=on_error
    ):
        if module.ispkg:
            imported = importlib.import_module(module.name)
            if not inspect.isfunction(getattr(imported, "setup", None)):
                # Skip extensions without a setup function
                continue

        yield module.name


EXTENSIONS = frozenset(walk_extensions())
