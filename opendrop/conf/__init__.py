import os

from opendrop.constants import ROOT_DIR

def conf(relpath):
    return os.path.join(ROOT_DIR, "conf", relpath)

PREFERENCES_FILENAME = conf("opendrop_parameters.json")
