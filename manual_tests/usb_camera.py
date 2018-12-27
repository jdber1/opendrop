import cv2

from opendrop.app.common.analysis_model.image_acquisition.default_types import USBCamera

CAMERA_INDEX_TO_TEST = 0

cam = USBCamera(cam_idx=CAMERA_INDEX_TO_TEST)

while(True):
    cv2.imshow('Press [q] to exit', cv2.cvtColor(cam.capture(), cv2.COLOR_RGB2BGR))
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
