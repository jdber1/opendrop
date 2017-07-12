import os

from opendrop.constants import ROOT_DIR

def resources(relpath):
    return os.path.join(ROOT_DIR, "resources", relpath)
