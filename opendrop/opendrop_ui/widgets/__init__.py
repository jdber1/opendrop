import _settings

from opendrop.opendrop_ui.widgets.utility.package_loader import load as _load
from opendrop.opendrop_ui.widgets.utility.preconfigure import preconfigure \
    as _preconfigure

_contents = _load(_settings)
for k, v in _contents.items():
    globals()[k] = v

def preconfigure(preconfig):
    return _preconfigure(_contents, preconfig)
