from customtkinter import *
from PIL import Image

from utils.image_handler import ImageHandler
from utils.config import *
from utils.validators import *
from .helper.theme import get_system_text_color
from .component.CTkXYFrame import *

class CaAnalysis(CTkFrame):
    def __init__(self, parent, user_input_data, **kwargs):
        super().__init__(parent, **kwargs)  
        self.user_input_data = user_input_data

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(0, weight=1)
        
        self.image_handler = ImageHandler()

        self.output = []
        
        self.preformed_methods = {key: value for key, value in user_input_data.analysis_methods_ca.items() if value}

        self.table_data = []  # List to store cell references
        self.create_table(parent=self, rows=user_input_data.number_of_frames, columns=len(self.preformed_methods)+1, headers=['Index'] + list(self.preformed_methods.keys()))

        self.images_frame = CTkFrame(self)
        self.images_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=(10, 0))

        self.current_index = 0
        self.highlight_row(self.current_index)
        self.initialize_image_display(self.images_frame)


    def create_table(self, parent, rows, columns, headers):
        # Create a frame for the table
        table_frame = CTkXYFrame(parent)
        table_frame.grid(row=0, column=0, pady=15, padx=20, sticky='nsew')

        # Create and place header labels
        for col in range(columns):
            header_label = CTkLabel(table_frame, text=headers[col], font=("Roboto", 14, "bold"))
            header_label.grid(row=0, column=col, padx=10, pady=5)

        # Create and place cell labels for each row
        for row in range(1, rows + 1):
            row_data = []
            for col in range(columns):
                text = ""
                if col == 0:
                    text = row
                cell_label = CTkLabel(table_frame, text=text, font=("Roboto", 12))
                cell_label.grid(row=row, column=col, padx=10, pady=5)
                row_data.append(cell_label)  # Store reference to the cell label
            self.table_data.append(row_data)

        self.table_data[len(self.output)][1].configure(text="PROCESSING...")

    def receive_output(self , extracted_data):
        self.output.append(extracted_data)

        for method in extracted_data.contact_angles.keys():
            preformed_method_list = list(self.preformed_methods.keys())
            
            if method in preformed_method_list:
                column_index = preformed_method_list.index(method)+1
                result = extracted_data.contact_angles[method]
                self.table_data[len(self.output)-1][column_index].configure(text=f"({result[LEFT_ANGLE]:.2f}, {result[RIGHT_ANGLE]:.2f})")
            else:
                print(f"Unknown method. Skipping the method.")
            

        if len(self.output) < self.user_input_data.number_of_frames:
            self.table_data[len(self.output)][1].configure(text="PROCESSING...")

    def highlight_row(self, row_index):
        # Reset all rows to default color
        for row in self.table_data:
            for cell in row:
                color = get_system_text_color()
                cell.configure(text_color=color)  # Reset to default background

        # Highlight the specified row
        if 0 <= row_index < len(self.table_data):
            for cell in self.table_data[row_index]:
                cell.configure(text_color="red")  # Change background color to yellow

    def initialize_image_display(self, frame):
        display_frame = CTkFrame(frame)
        display_frame.grid(sticky="nsew", padx=15, pady=(10, 0))

        self.image_label = CTkLabel(display_frame, text="", fg_color="lightgrey", width=400, height=300)
        self.image_label.grid(padx=10, pady=(10, 5))

        file_name = os.path.basename(self.user_input_data.import_files[self.current_index])
        self.name_label = CTkLabel(display_frame, text=file_name)
        self.name_label.grid()

        self.image_navigation_frame = CTkFrame(display_frame)
        self.image_navigation_frame.grid(pady=20)

        self.prev_button = CTkButton(self.image_navigation_frame, text="<", command=lambda: self.change_image(-1), width=3)
        self.prev_button.grid(row=0, column=0, padx=5, pady=5)

        self.index_entry = CTkEntry(self.image_navigation_frame, width=5)
        self.index_entry.grid(row=0, column=1, padx=5, pady=5)
        self.index_entry.bind("<Return>", lambda event: self.update_index_from_entry())
        self.index_entry.insert(0, str(self.current_index + 1))

        self.navigation_label = CTkLabel(self.image_navigation_frame, text=f" of {self.user_input_data.number_of_frames}", font=("Arial", 12))
        self.navigation_label.grid(row=0, column=2, padx=5, pady=5)

        self.next_button = CTkButton(self.image_navigation_frame, text=">", command=lambda: self.change_image(1), width=3)
        self.next_button.grid(row=0, column=3, padx=5, pady=5)

        self.load_image(self.user_input_data.import_files[self.current_index])

    def load_image(self, selected_image):
        """Load and display the selected image."""
        try:
            self.current_image = Image.open(selected_image)
            self.display_image()
        except FileNotFoundError:
            print(f"Error: The image file {selected_image} was not found.")
            self.current_image = None

    def display_image(self):
        """Display the currently loaded image."""
        width, height = self.current_image.size
        new_width, new_height = self.image_handler.get_fitting_dimensions(width, height)
        self.tk_image = CTkImage(self.current_image, size=(new_width, new_height))
        self.image_label.configure(image=self.tk_image)
        # Keep a reference to avoid garbage collection
        self.image_label.image = self.tk_image

    def change_image(self, direction):
        """Change the currently displayed image based on the direction."""
        if self.user_input_data.import_files:
            self.current_index = (
                self.current_index + direction) % self.user_input_data.number_of_frames
            # Load the new image
            self.load_image(
                self.user_input_data.import_files[self.current_index])
            self.update_index_entry()  # Update the entry with the current index
            file_name = os.path.basename(
                self.user_input_data.import_files[self.current_index])
            self.name_label.configure(text=file_name)

            self.highlight_row(self.current_index)

    def update_index_from_entry(self):
        """Update current index based on user input in the entry."""
        try:
            new_index = int(self.index_entry.get()) - \
                1  # Convert to zero-based index
            if 0 <= new_index < self.user_input_data.number_of_frames:
                self.current_index = new_index
                # Load the new image
                self.load_image(
                    self.user_input_data.import_files[self.current_index])
            else:
                print("Index out of range.")
        except ValueError:
            print("Invalid input. Please enter a number.")

        self.update_index_entry()  # Update the entry display

    def update_index_entry(self):
        """Update the index entry to reflect the current index."""
        self.index_entry.delete(0, 'end')  # Clear the current entry
        # Insert the new index (1-based)
        self.index_entry.insert(0, str(self.current_index + 1))