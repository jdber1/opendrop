import _settings

from opendrop.opendrop_ui.widgets.import_utility.package_loader import load as _load
from opendrop.opendrop_ui.widgets.import_utility.preconfigure import preconfigure \
    as _preconfigure

_contents = _load(_settings)
for k, v in _contents.items():
    globals()[k] = v

def preconfigure(preconfig):
    return _preconfigure(_contents, preconfig)
