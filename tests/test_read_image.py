import pytest
import numpy as np
import sys
import os
from unittest import mock

from unittest.mock import patch,MagicMock


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.read_image import get_image,save_image,import_from_source,image_from_Flea3,image_from_harddrive,get_import_filename,image_from_camera,grabanimage


# Fixture to create a mock ExperimentalDrop object
@pytest.fixture
def mock_experimental_drop():
    class ExperimentalDrop:
        image = None
        time = None
    return ExperimentalDrop()

# Fixture to create a mock ExperimentalSetup object
@pytest.fixture
def mock_experimental_setup():
    class ExperimentalSetup:
        image_source = "Local images"
        directory_string = "test_directory"
        filename = "test_image.png"
        import_files = ["test_image.png"]
        save_images_boole = True
        create_folder_boole = True
        time_string = "2024-09-08-120000"
    return ExperimentalSetup()

# Test get_image function
@patch("cv2.imwrite")
@patch("os.makedirs")
def test_get_image(mock_makedirs, mock_imwrite, mock_experimental_drop, mock_experimental_setup):
    get_image(mock_experimental_drop, mock_experimental_setup, 0)
    mock_makedirs.assert_called_once()

    # Reset the mock so we only check the next call
    mock_makedirs.reset_mock()

    # Test without create_folder_boole
    mock_experimental_setup.create_folder_boole = False
    get_image(mock_experimental_drop, mock_experimental_setup, 0)
    mock_makedirs.assert_not_called()

# Test save_image function
def test_save_image(mock_experimental_drop, mock_experimental_setup):
    mock_experimental_drop.image = np.zeros((100, 100, 3), dtype=np.uint8)
    with patch("cv2.imwrite") as mock_imwrite:
        save_image(mock_experimental_drop, mock_experimental_setup, 1)
        mock_imwrite.assert_called_once()

# Test import_from_source with local images
@patch("modules.read_image.image_from_harddrive")
def test_import_from_source_local(mock_image_from_harddrive, mock_experimental_drop, mock_experimental_setup):
    import_from_source(mock_experimental_drop, mock_experimental_setup, 0)
    mock_image_from_harddrive.assert_called_once()

# Test image_from_Flea3 function
@patch("subprocess.call")
@patch("cv2.imread")
def test_image_from_Flea3(mock_imread, mock_subprocess, mock_experimental_drop):
    mock_imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    image_from_Flea3(mock_experimental_drop)
    mock_subprocess.assert_called_once_with(["./FCGrab"])
    mock_imread.assert_called_once_with("FCG.pgm", 1)

# Test image_from_harddrive function
def test_image_from_harddrive(mock_experimental_drop, mock_experimental_setup):
    with patch("cv2.imread", return_value=np.zeros((100, 100, 3), dtype=np.uint8)) as mock_imread:
        image_from_harddrive(mock_experimental_drop, mock_experimental_setup, 0)
        mock_imread.assert_called_once_with("test_image.png", 1)

# Test get_import_filename function
def test_get_import_filename(mock_experimental_setup):
    filename = get_import_filename(mock_experimental_setup, 0)
    assert filename == "test_image.png"

# Test image_from_camera function
@patch("modules.read_image.grabanimage")
def test_image_from_camera(mock_grabanimage, mock_experimental_drop):
    with patch("cv2.imread", return_value=np.zeros((100, 100, 3), dtype=np.uint8)) as mock_imread:
        image_from_camera(mock_experimental_drop)
        mock_grabanimage.assert_called_once()
        mock_imread.assert_called_once_with("USBtemp.png", 1)

# Test grabanimage function
@patch("cv2.VideoCapture")
def test_grabanimage(mock_VideoCapture):
    mock_camera = MagicMock()
    mock_VideoCapture.return_value = mock_camera
    mock_camera.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
    with patch("cv2.imwrite") as mock_imwrite:
        grabanimage()
        mock_camera.read.assert_called()
        mock_imwrite.assert_called_once_with("USBtemp.png", mock_camera.read.return_value[1])

# Run the tests when this script is executed directly
if __name__ == "__main__":
    pytest.main()
