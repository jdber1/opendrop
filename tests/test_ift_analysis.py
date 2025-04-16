import pytest
import time
from customtkinter import CTk, CTkFrame
from views.ift_analysis import IftAnalysis
from modules.core.classes import ExperimentalSetup


@pytest.fixture
def app():
    """Fixture to create a tkinter application instance in fullscreen mode for testing."""
    app = CTk()

    # Set the application to full-screen mode
    app.attributes("-fullscreen", True)

    # Create a frame within the full-screen window
    frame = CTkFrame(app)
    frame.pack(fill='both', expand=True)

    # Ensure that the application is rendered properly
    app.update()

    # Yield the frame for the test
    yield frame

    # Cleanup after the test
    app.destroy()


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
def test_create_results_tab(app, import_files):
    """Test the creation of the results tab."""
    user_input_data = ExperimentalSetup()
    user_input_data.import_files = import_files

    analysis = IftAnalysis(app, user_input_data)
    analysis.create_results_tab(analysis.tab_view.tab("Results"))

    results_tab = analysis.tab_view.tab("Results")
    assert results_tab is not None  # Check if the Graphs tab exists
    # Ensure the tab has children (elements)


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


@pytest.mark.parametrize("import_files", [
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp"]),
    (["experimental_data_set/3.bmp"]),
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp",
     "experimental_data_set/10.bmp"]),
])
def test_create_image_frame(app, import_files):
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


@pytest.mark.parametrize("import_files", [
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp"]),
    (["experimental_data_set/3.bmp"]),
    (["experimental_data_set/3.bmp", "experimental_data_set/5.bmp",
        "experimental_data_set/10.bmp"]),
])
def test_create_residuals_frame(app, import_files):
    """Test the creation of the residuals frame."""
    user_input_data = ExperimentalSetup()
    user_input_data.import_files = import_files

    analysis = IftAnalysis(app, user_input_data)
    analysis.create_residuals_frame(analysis.tab_view.tab("Results"))

    residuals_frame = analysis.residuals_frame
    assert residuals_frame is not None  # Ensure the image frame is created
    # Check if the frame has a width

    time.sleep(0.1)
    assert residuals_frame.winfo_width() > 0
