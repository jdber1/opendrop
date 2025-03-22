import os

IMAGE_EXTENSION = '.png'

BACKGROUND_COLOR = 'gray90'
VERSION = '1.0'

DROP_ID_OPTIONS = ["Automated", "User-selected"]
THRESHOLD_OPTIONS = ["Automated", "User-selected"]
BASELINE_OPTIONS = ["Automated", "User-selected"]
NEEDLE_OPTIONS = ['0.7176', '1.270', '1.651']
IMAGE_SOURCE_OPTIONS = ["Flea3", "USB camera", "Local images"]
EDGEFINDER_OPTIONS = ["OpenCV", "Subpixel", "Both"]

PATH_TO_SCRIPT = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..')
PATH_TO_FILE = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "parameters.csv")

# FONT_FRAME_LABEL = ("Helvetica", 16, "BOLD")
FONT_FRAME_LABEL = '*-*-medium-r-normal--*-160-*'

LABEL_WIDTH = 29
ENTRY_WIDTH = 11