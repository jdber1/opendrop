import pytest
import time
import tkinter as tk
from customtkinter import CTk, CTkFrame
from views.ift_analysis import IftAnalysis


@pytest.fixture
def app():
    """Fixture to create a tkinter application instance for testing."""
    # root = tk.Tk()
    app = CTk()
    frame = CTkFrame(app, width=700)
    frame.pack(fill='both', expand=True)
    app.update()
    yield frame  # Use frame instead of app
    app.destroy()  # Cleanup after tests


def test_if_analysis_creation(app):
    """Test the creation of IftAnalysis."""
    analysis = IftAnalysis(app)
    # Check if the instance is created
    assert isinstance(analysis, IftAnalysis)
    assert analysis.tab_view  # Ensure tab view is created


def test_create_table_view(app):
    """Test the creation of table view in IftAnalysis."""
    analysis = IftAnalysis(app)
    analysis.create_table_view()

    results_tab = analysis.tab_view.tab("Results")
    assert results_tab is not None  # Check if the Results tab exists
    # Ensure the tab has children (elements)
    assert len(results_tab.winfo_children()) > 0


def test_create_visualisation_frame(app):
    """Test the creation of the visualisation frame."""
    analysis = IftAnalysis(app)
    analysis.create_visualisation_frame(analysis.tab_view.tab("Results"))

    # Check if the visualisation frame is created
    images_frame = analysis.tab_view.tab("Results").winfo_children()[-1]
    assert isinstance(images_frame, CTkFrame)  # Ensure it's a CTkFrame
    assert images_frame.winfo_width() <= 400  # Check if width is set to 400


def test_create_graph_view(app):
    """Test the creation of the graph view."""
    analysis = IftAnalysis(app)
    analysis.create_graph_view()

    graphs_tab = analysis.tab_view.tab("Graphs")
    assert graphs_tab is not None  # Check if the Graphs tab exists
    # Ensure the tab has children (elements)
    assert len(graphs_tab.winfo_children()) > 0


@pytest.mark.parametrize("image_path", [
    'experimental_data_set\\5.bmp',  # Test path
])
def test_create_image_frame(app, image_path):
    """Test the creation of the image frame."""
    analysis = IftAnalysis(app)
    analysis.create_image_frame(analysis.tab_view.tab("Results"), image_path)

    image_frame = analysis.image_frame
    assert image_frame is not None  # Ensure the image frame is created
    # Check if the frame has a width

    time.sleep(0.1)
    assert image_frame.winfo_width() > 0


@pytest.mark.parametrize("event", [None, "resize"])
def test_resize_image(app, event):
    """Test the resizing of the image."""
    analysis = IftAnalysis(app)
    analysis.create_image_frame(analysis.tab_view.tab("Results"))

    # Resize the image
    analysis.resize_image(event)

    assert analysis.ctk_image is not None  # Check if the image is set

    analysis.update()

    # Get width and height from the PIL image
    image_width = analysis.ctk_image._light_image.width
    image_height = analysis.ctk_image._light_image.height

    assert analysis.aspect_ratio == image_height / \
        image_width  # Check the aspect ratio
