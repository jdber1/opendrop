from customtkinter import CTkImage
from customtkinter import CTkFrame, CTkScrollableFrame, CTkTabview, CTkLabel, CTkImage
from PIL import Image
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

        # Bind the window resizing event
        self.bind("<Configure>", self.resize_image)

    def create_table_view(self):
        results_tab = self.tab_view.tab("Results")
        main_frame = CTkFrame(results_tab)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.create_table_frame(main_frame)
        self.create_visualisation_frame(main_frame)

    def create_table_frame(self, parent):
        table_frame = CTkScrollableFrame(parent)
        table_frame.pack(side="left", padx=10, fill="both", expand=True)
        headings = ["Time", "IFT", "V", "SA", "Bond", "Worth"]
        for j, heading in enumerate(headings):
            cell = CTkLabel(table_frame, text=heading)
            cell.grid(row=0, column=j, padx=10, pady=10, sticky="nsew")
        for i in range(1, 6):
            for j in range(len(headings)):
                cell = CTkLabel(table_frame, text=f"Cell ({i},{j+1})")
                cell.grid(row=i, column=j, padx=10, pady=10, sticky="nsew")
        for j in range(len(headings)):
            table_frame.grid_columnconfigure(j, weight=1)
        for i in range(6):
            table_frame.grid_rowconfigure(i, weight=1)

    def create_visualisation_frame(self, parent):
        images_frame = CTkFrame(parent)
        images_frame.pack(side="right", padx=10, fill="both", expand=True)
        images_frame.grid_rowconfigure(0, weight=1)
        images_frame.grid_rowconfigure(1, weight=1)
        self.create_image_frame(images_frame)
        self.create_residuals_frame(images_frame)

    def create_image_frame(self, parent, path_to_image='experimental_data_set\\5.bmp'):
        self.image_frame = CTkFrame(parent)
        self.image_frame.grid(row=0, column=0, sticky="nsew")

        # Load the original image
        self.original_image = Image.open(path_to_image)
        self.aspect_ratio = self.original_image.height / self.original_image.width

        # Create a label to display the image
        self.image_label = CTkLabel(self.image_frame, text="")
        self.image_label.pack(fill="both", expand=True)

        # Initial call to display the image
        self.resize_image()

    def resize_image(self, event=None):
        if self.tab_view.winfo_width() > 0 and self.tab_view.winfo_height() > 0:
            # Calculate new dimensions, keeping aspect ratio
            print(
                f'Original Image height: {self.original_image.height}, width: {self.original_image.width}')
            print(
                f"Tab height: {self.tab_view.winfo_height()}, width: {self.tab_view.winfo_width()}")
            image_width = 400  # self.tab_view.winfo_width() / 4
            image_height = self.aspect_ratio * image_width

            # if image_height > self.tab_view.winfo_height() / 2:
            #     image_height = self.tab_view.winfo_height() / 2
            #     image_width = image_height / self.aspect_ratio

            # # Ensure full image is shown
            # image_width += 5
            # image_height += 5

            # Resize the original image
            resized_image = self.original_image.resize(
                (int(image_width), int(image_height)), Image.LANCZOS)

            # Create a CTkImage from the resized image
            ctk_image = CTkImage(light_image=resized_image, dark_image=resized_image, size=(
                int(image_width), int(image_height)))

            print(
                f'Resized Image height: {image_height}, width: {image_width}')
            # Update the image label with CTkImage
            self.image_label.configure(image=ctk_image)
            self.image_label.image = ctk_image  # Prevent garbage collection

    def create_residuals_frame(self, parent):
        residuals_frame = CTkFrame(parent)
        residuals_frame.grid(row=1, column=0, sticky="nsew")

        # Create the figure and axis
        # Size can be adjusted as needed
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [2, 5, 10])  # Example data for the residuals
        ax.set_title('Residuals')

        # Create a canvas for the figure
        canvas = FigureCanvasTkAgg(fig, residuals_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Create and pack the navigation toolbar
        toolbar = NavigationToolbar2Tk(canvas, residuals_frame)
        toolbar.update()
        # Ensure the canvas is packed after toolbar
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Draw the canvas to show the figure
        canvas.draw()

    def create_graph_view(self):
        graphs_tab = self.tab_view.tab("Graphs")
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [1, 4, 9])
        canvas = FigureCanvasTkAgg(fig, graphs_tab)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(canvas, graphs_tab)
        toolbar.update()
        canvas.draw()
