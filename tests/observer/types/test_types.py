import importlib
import inspect
import pkgutil

from opendrop import observer
from opendrop.observer.bases import ObserverProvider

OBSERVERS_PKG = observer.types


def get_providers(mod):
    mod = importlib.import_module(mod) if isinstance(mod, str) else mod

    providers = []

    for name in dir(mod):
        obj = getattr(mod, name)

        if inspect.isclass(obj) and issubclass(obj, ObserverProvider) and obj.__module__ == mod.__name__:
            providers.append(obj)

    if hasattr(mod, '__path__'):
        for loader, name, is_pkg in pkgutil.walk_packages(mod.__path__):
            full_name = mod.__name__ + '.' + name
            providers += get_providers(full_name)

    return providers


# Confirm that the number of `ObserverProvider`s defined in `OBSERVER_PKG` matches with the number of types in
# `ObserverType`
def test_types_count():
    scraped_providers_count = len(get_providers(OBSERVERS_PKG))
    observer_type_count = len(observer.types.get_all_types())

    assert(scraped_providers_count == observer_type_count)


# Test that some observers are accessible from `observer.types`, to make sure it's kind of working.
def test_can_access_some():
    assert observer.types.USB_CAMERA