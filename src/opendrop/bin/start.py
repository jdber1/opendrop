#!/usr/bin/env python

# If not installed in site-packages
import os
import sys

from src.opendrop import app

sys.path.append(os.path.join(sys.path[0], "..", ".."))

app.main()
