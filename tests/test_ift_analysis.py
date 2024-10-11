import pytest
import time
from customtkinter import CTk, CTkFrame
from views.ift_analysis import IftAnalysis
from modules.classes import ExperimentalSetup


@pytest.fixture
def app():
    """Fixture to create a tkinter application instance for testing."""
    app = CTk()
    frame = CTkFrame(app, width=1000, height=600)
    frame.pack(fill='both', expand=True)
    app.update()
    yield frame  # Use frame instead of app
    app.destroy()  # Cleanup after tests


@pytest.mark.parametrize("import_files", [
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp"]),
    (["experimental_data_set/3.bmp"]),
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp",
     "experimental_data_set/10.bmp"]),
])
def test_if_analysis_creation(app, import_files):
    """Test the creation of IftAnalysis."""
    user_input_data = ExperimentalSetup()
    user_input_data.import_files = import_files

    analysis = IftAnalysis(app, user_input_data)
    # Check if the instance is created
    assert isinstance(analysis, IftAnalysis)
    assert analysis.tab_view  # Ensure tab view is created


@pytest.mark.parametrize("import_files", [
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp"]),
    (["experimental_data_set/3.bmp"]),
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp",
     "experimental_data_set/10.bmp"]),
])
def test_create_table(app, import_files):
    """Test the creation of table in IftAnalysis."""
    user_input_data = ExperimentalSetup()
    user_input_data.import_files = import_files

    analysis = IftAnalysis(app, user_input_data)
    analysis.create_table(analysis.tab_view.tab("Results"))

    results_tab = analysis.tab_view.tab("Results")
    assert results_tab is not None  # Check if the Results tab exists
    # Ensure the tab has children (elements)
    assert len(results_tab.winfo_children()) > 0


@pytest.mark.parametrize("import_files", [
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp"]),
    (["experimental_data_set/3.bmp"]),
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp",
     "experimental_data_set/10.bmp"]),
])
def test_create_visualisation_frame(app, import_files):
    """Test the creation of the visualisation frame."""
    user_input_data = ExperimentalSetup()
    user_input_data.import_files = import_files

    analysis = IftAnalysis(app, user_input_data)
    analysis.create_visualisation_frame(analysis.tab_view.tab("Results"))

    # Check if the visualisation frame is created
    images_frame = analysis.tab_view.tab("Results").winfo_children()[-1]
    assert isinstance(images_frame, CTkFrame)  # Ensure it's a CTkFrame
    assert images_frame.winfo_width() <= 400  # Check if width is set to 400


@pytest.mark.parametrize("import_files", [
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp"]),
    (["experimental_data_set/3.bmp"]),
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp",
     "experimental_data_set/10.bmp"]),
])
def test_create_graph_tab(app, import_files):
    """Test the creation of the graph view."""
    user_input_data = ExperimentalSetup()
    user_input_data.import_files = import_files

    analysis = IftAnalysis(app, user_input_data)
    analysis.create_graph_tab(analysis.tab_view.tab("Graphs"))

    graphs_tab = analysis.tab_view.tab("Graphs")
    assert graphs_tab is not None  # Check if the Graphs tab exists
    # Ensure the tab has children (elements)
    assert len(graphs_tab.winfo_children()) > 0


@pytest.mark.parametrize("image_path", [
    'experimental_data_set\\5.bmp',  # Test path
])
@pytest.mark.parametrize("import_files", [
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp"]),
    (["experimental_data_set/3.bmp"]),
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp",
     "experimental_data_set/10.bmp"]),
])
def test_create_image_frame(app, image_path, import_files):
    """Test the creation of the image frame."""
    user_input_data = ExperimentalSetup()
    user_input_data.import_files = import_files

    analysis = IftAnalysis(app, user_input_data)
    analysis.create_image_frame(analysis.tab_view.tab("Results"))

    image_frame = analysis.image_frame
    assert image_frame is not None  # Ensure the image frame is created
    # Check if the frame has a width

    time.sleep(0.1)
    assert image_frame.winfo_width() > 0


@pytest.mark.parametrize("event", [None, "resize"])
@pytest.mark.parametrize("import_files", [
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp"]),
    (["experimental_data_set/3.bmp"]),
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp",
     "experimental_data_set/10.bmp"]),
])
def test_resize_image(app, import_files, event):
    """Test the resizing of the image."""
    user_input_data = ExperimentalSetup()
    user_input_data.import_files = import_files

    analysis = IftAnalysis(app, user_input_data)
    analysis.create_image_frame(analysis.tab_view.tab("Results"))

    # Resize the image
    analysis.resize_image(event)

    assert analysis.ctk_image is not None  # Check if the image is set

    # Get width and height from the PIL image
    image_width = analysis.ctk_image._light_image.width
    image_height = analysis.ctk_image._light_image.height

    assert analysis.aspect_ratio == image_height / \
        image_width  # Check the aspect ratio
