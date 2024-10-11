import pytest
from unittest import mock
from customtkinter import CTkFrame
from views.ift_analysis import IftAnalysis
from PIL import Image


@pytest.fixture
def analysis():
    # Create a mock parent widget with a 'tk' attribute
    mock_ctk_frame = mock.Mock(spec=CTkFrame)
    mock_ctk_frame.tk = mock.Mock()  # Add 'tk' attribute to the mock
    # Initialize the IftAnalysis instance
    return IftAnalysis(mock_ctk_frame)


@mock.patch('PIL.Image.open')  # Patch Image.open for the test
def test_create_image_frame(mock_open, analysis):
    mock_image = mock.MagicMock()
    mock_open.return_value = mock_image

    # Create an image frame
    analysis.create_image_frame(analysis)

    # Check if the canvas is created
    assert 'Canvas' in analysis.children

    # Check if the image is set in the canvas
    assert analysis.tk_image is not None

    # Ensure that the image was opened
    mock_open.assert_called_once()


def test_create_table_frame(analysis):
    # Test the creation of the table frame
    analysis.create_table_frame(analysis)

    # Check if the table frame is created and packed
    assert analysis.children is not None
    assert 'CTkScrollableFrame' in analysis.children

    # Check if the headings are created
    headings = ["Time", "IFT", "V", "SA", "Bond", "Worth"]
    scrollable_frame = analysis.children['CTkScrollableFrame']
    heading_labels = [label.cget('text')
                      for label in scrollable_frame.grid_slaves()]

    for heading in headings:
        assert heading in heading_labels
