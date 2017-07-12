#!/usr/bin/env python

# If not installed in site-packages
import os, sys
sys.path.append(os.path.join(sys.path[0], "..", ".."))

from opendrop.lib import opendrop_ui

opendrop_ui.main()
