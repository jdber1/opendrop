from customtkinter import CTkFrame, CTkScrollableFrame, CTkTabview, CTkLabel
from tkinter import Canvas
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class IftAnalysis(CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        # Create and configure the CTkTabView
        self.tab_view = CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=20)

        # Add "Results" and "Graphs" tabs
        self.tab_view.add("Results")
        self.tab_view.add("Graphs")

        # Initialize content for each tab
        self.create_table_view()
        self.create_graph_view()

    def create_table_view(self):
        results_tab = self.tab_view.tab("Results")

        # Create a frame to organize two sections of equal height
        main_frame = CTkFrame(results_tab)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.create_table_frame(main_frame)
        self.create_visualisation_frame(main_frame)

    def create_table_frame(self, parent):
        # Create a frame for the table
        table_frame = CTkScrollableFrame(parent)
        table_frame.pack(side="left", padx=10, fill="both", expand=True)

        # Create headings for the table
        headings = ["Time", "IFT", "V", "SA", "Bond", "Worth"]

        # Add heading labels to the table using grid
        for j, heading in enumerate(headings):
            cell = CTkLabel(table_frame, text=heading)
            cell.grid(row=0, column=j, padx=10, pady=10, sticky="nsew")

        # Create a grid for the data in the table
        for i in range(1, 6):  # Start from row 1 to leave row 0 for headings
            for j in range(len(headings)):
                cell = CTkLabel(table_frame, text=f"Cell ({i},{j+1})")
                cell.grid(row=i, column=j, padx=10, pady=10, sticky="nsew")

        # Configure the grid to expand and center the table
        for j in range(len(headings)):
            # Allow columns to expand equally
            table_frame.grid_columnconfigure(j, weight=1)

        for i in range(6):  # Total rows (1 for headings + 5 for data)
            # Allow rows to expand equally
            table_frame.grid_rowconfigure(i, weight=1)

        # Optionally, set a minimum size for each cell to ensure content fits
        for j in range(len(headings)):
            for i in range(6):
                cell = CTkLabel(
                    table_frame, text=f"Cell ({i},{j+1})" if i > 0 else headings[j])
                cell.grid(row=i, column=j, padx=10, pady=10, sticky="nsew")
                cell.configure(width=100)  # Set a fixed width for each cell

    def create_visualisation_frame(self, parent):
        # Create a frame for both graphs/images
        images_frame = CTkFrame(parent)
        images_frame.pack(side="right", padx=10, fill="both", expand=True)

        # Configure grid for equal height of child frames
        # Allow the first row to expand
        images_frame.grid_rowconfigure(0, weight=1)
        # Allow the second row to expand
        images_frame.grid_rowconfigure(1, weight=1)

        # Create frames for images and residuals
        self.create_image_frame(images_frame)
        self.create_residuals_frame(images_frame)

    def create_image_frame(self, parent, path_to_image="experimental_data_set\5.bmp"):
        image_frame = CTkFrame(parent)
        # Place in the first row
        image_frame.grid(row=0, column=0, sticky="nsew")

        # Load the image
        self.original_image = Image.open(path_to_image)
        self.zoom_level = 1.0  # Initial zoom level
        self.canvas = Canvas(image_frame)
        self.canvas.pack(fill="both", expand=True)

        # Create a Tkinter-compatible photo image
        self.tk_image = ImageTk.PhotoImage(self.original_image)
        self.image_id = self.canvas.create_image(
            0, 0, anchor="nw", image=self.tk_image)

    def create_residuals_frame(self, parent):
        # Create a frame for the second graph
        residuals_frame = CTkFrame(parent)
        # Place in the second row
        residuals_frame.grid(row=1, column=0, sticky="nsew")

        # Create the graph
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [2, 5, 10])  # Sample data for graph
        ax.set_title('Residuals')
        ax.set_xlabel('X-axis Label')
        ax.set_ylabel('Y-axis Label')
        fig.tight_layout()

        # Create a canvas to hold the graph
        canvas = FigureCanvasTkAgg(fig, residuals_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Add a navigation toolbar
        toolbar = NavigationToolbar2Tk(canvas, residuals_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        canvas.draw()

    def create_graph_view(self):
        graphs_tab = self.tab_view.tab("Graphs")

        # Create a sample graph
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [1, 4, 9])  # Sample data for graph
        ax.set_xlabel('X-axis Label')
        ax.set_ylabel('Y-axis Label')

        # Create a canvas to hold the graph in the Graphs tab
        canvas = FigureCanvasTkAgg(fig, graphs_tab)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Add a navigation toolbar
        toolbar = NavigationToolbar2Tk(canvas, graphs_tab)
        toolbar.update()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        canvas.draw()
