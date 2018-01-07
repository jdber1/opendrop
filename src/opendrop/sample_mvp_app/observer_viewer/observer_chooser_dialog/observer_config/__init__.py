import sys

from opendrop.utility.misc import recursive_load

current_module = sys.modules[__name__]

# Recursively load all the modules in `observer_config` so they get returned in ObserverConfigView.__subclasses__()
recursive_load(current_module)
