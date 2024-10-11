from customtkinter import CTkImage, CTkFrame, CTkScrollableFrame, CTkTabview, CTkLabel
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from .component.imageGallery import ImageGallery


class IftAnalysis(CTkFrame):
    def __init__(self, parent, user_input_data, **kwargs):
        super().__init__(parent, **kwargs)

        self.user_input_data = user_input_data
        self.pack(fill="both", expand=True)

        # Create tabs
        self.tab_view = CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=20)

        # Add "Results" and "Graphs" tabs
        self.tab_view.add("Results")
        self.tab_view.add("Graphs")

        # Initialize content for each tab
        self.create_results_tab(self.tab_view.tab("Results"))
        self.create_graph_tab(self.tab_view.tab("Graphs"))

    def create_results_tab(self, parent):
        """Create a split frame containing a Table on the left and Residuals with base image on the right into the parent frame"""

        # Configure the grid to allow expansion for both columns
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)  # Left column for table
        parent.grid_columnconfigure(
            1, weight=1)  # Right column for visuals

        # Table can be large, so scrollable
        self.table_frame = CTkScrollableFrame(parent)
        self.table_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=(
            10, 0))  # Left side for table

        self.visualisation_frame = CTkFrame(parent)
        self.visualisation_frame.grid(row=0, column=1, padx=10, sticky="nsew")
        self.visualisation_frame.grid_rowconfigure(0, weight=1)
        self.visualisation_frame.grid_rowconfigure(1, weight=1)

        self.create_table(self.table_frame)
        self.create_image_frame(self.visualisation_frame)
        self.create_residuals_frame(self.visualisation_frame)

    def create_table(self, parent_frame):
        """Create a table into the parent frame. Headings are: Time, IFT, V, SA, Bond, Worth"""

        # Configure the row and column weights for expansion
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)

        headings = ["Time", "IFT", "V", "SA", "Bond", "Worth"]
        for j, heading in enumerate(headings):
            cell = CTkLabel(parent_frame, text=heading)
            cell.grid(row=0, column=j, padx=10, pady=10, sticky="nsew")

        for i in range(1, 21):  # Adjusted to create more rows for better scrolling
            for j in range(len(headings)):
                cell = CTkLabel(parent_frame, text=f"Cell ({i},{j + 1})")
                cell.grid(row=i, column=j, padx=10, pady=10, sticky="nsew")

        for j in range(len(headings)):
            parent_frame.grid_columnconfigure(j, weight=1)

        # Set row configuration to allow for vertical scrolling
        for i in range(21):  # Adjust the range as needed
            parent_frame.grid_rowconfigure(i, weight=1)

    def create_image_frame(self, parent):
        """Create an Image Gallery that allows back and forth between base images into the parent frame"""
        self.image_frame = ImageGallery(
            parent, self.user_input_data.import_files)
        self.image_frame.grid(row=0, column=0, sticky="nsew")

    def create_residuals_frame(self, parent):
        """Create a graph containing residuals into the parent frame. Graph is of same size as the Image Gallery."""

        residuals_frame = CTkFrame(parent)
        residuals_frame.grid(row=1, column=0, sticky="nsew")

        # Create the figure and axis
        # width, height = self.image_frame.image_label.image.size
        fig, ax = plt.subplots(
            figsize=(4, 3))
        ax.plot([1, 2, 3], [2, 5, 10])  # Example data for the residuals
        ax.set_title('Residuals')

        # Create a canvas for the figure
        canvas = FigureCanvasTkAgg(fig, residuals_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Create and pack the navigation toolbar
        toolbar = NavigationToolbar2Tk(canvas, residuals_frame)
        toolbar.update()

        # Ensure the canvas is packed after the toolbar
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Draw the canvas to show the figure
        canvas.draw()

    def create_graph_tab(self, parent):
        """Create a full sized graph into the parent frame"""

        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [1, 4, 9])

        # Create the canvas for the figure
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Create and pack the navigation toolbar
        toolbar = NavigationToolbar2Tk(canvas, parent)
        toolbar.update()
        canvas.draw()
