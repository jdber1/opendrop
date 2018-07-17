from typing import List

from opendrop.observer.bases import ObserverType
from opendrop.utility.misc import recursive_load

# Recursively load all the modules in `types` so they define their `ObserverType` constants in this module
recursive_load('opendrop.observer.types')


def get_all_types() -> List[ObserverType]:
    types = []

    for k, v in globals().items():
        if not k.startswith('_') and isinstance(v, ObserverType):
            types.append(v)

    return types
