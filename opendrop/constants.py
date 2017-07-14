import os

from collections import namedtuple

from opendrop.utility.enums import enum

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Using namedtuples as enums

OperationMode = namedtuple("OperationMode",
    ("PENDANT", "SESSILE", "CONAN", "CONAN_NEEDLE"))(*range(4))

ImageSourceOption = namedtuple("ImageSourceOptions",
    ("FLEA3", "USB_CAMERA", "LOCAL_IMAGES")) \
    ("Flea3", "USB camera", "Local images")
