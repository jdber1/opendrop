import os

VERSION = '1.0'

AUTO_MANUAL_OPTIONS = ["Automated", "User-selected"] 
DROP_ID_OPTIONS = ["Automated", "User-selected"]
THRESHOLD_OPTIONS = ["Automated", "User-selected"]
BASELINE_OPTIONS = ["Automated", "User-selected"]
NEEDLE_OPTIONS = ['0.7176', '1.270', '1.651']
FILE_SOURCE_OPTIONS_CA = ["Local images", "Flea3", "USB camera"]
FILE_SOURCE_OPTIONS_IFT = ["Local images", "cv2.VideoCapture", "GenlCam"]
EDGEFINDER_OPTIONS = ["OpenCV", "Subpixel", "Both"]

#OPENDROP
INTERFACIAL_TENSION = "Interfacial Tension"

TANGENT_FIT = "tangent fit"
POLYNOMIAL_FIT = "polynomial fit"
CIRCLE_FIT = "circle fit"
ELLIPSE_FIT = "ellipse fit"
YL_FIT = "YL fit"
ML_MODEL = "ML model"

LEFT_ANGLE = 'left angle'
RIGHT_ANGLE = 'right angle'

PATH_TO_SCRIPT = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..')
PATH_TO_FILE = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "parameters.csv")

# FONT_FRAME_LABEL = ("Helvetica", 16, "BOLD")
FONT_FRAME_LABEL = '*-*-medium-r-normal--*-160-*'

LABEL_WIDTH = 29
ENTRY_WIDTH = 11

DELTA_TOL = 1.e-6
GRADIENT_TOL = 1.e-6
MAXIMUM_FITTING_STEPS = 10
OBJECTIVE_TOL = 1.e-4
ARCLENGTH_TOL = 1.e-6
MAXIMUM_ARCLENGTH_STEPS = 10
NEEDLE_TOL = 1.e-4
NEEDLE_STEPS = 20

IMAGE_TYPE = [
            ("Image Files", "*.png"),
            ("Image Files", "*.jpg"),
            ("Image Files", "*.jpeg"),
            ("Image Files", "*.gif"),
            ("Image Files", "*.bmp")
        ]