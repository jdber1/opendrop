import customtkinter as ctk
import tkinter as tk

class CTkTablePopup(ctk.CTkToplevel):
    _instance = None  # Class variable to track the instance

    def __new__(cls, *args, **kwargs):
        # Only create a new instance if one doesn't exist
        if cls._instance is None:
            cls._instance = super(CTkTablePopup, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, parent, headers, data, on_row_select, title="Select a row", **kwargs):
        # If the instance is already created, prevent reinitialization
        if not hasattr(self, 'initialized'):
            super().__init__(parent, **kwargs)
            self.title(title)
            self.geometry("760x300")
            self.on_row_select = on_row_select

            # Scrollable frame to hold the table rows
            self.table_frame = ctk.CTkScrollableFrame(self, width=740, height=200)
            self.table_frame.pack(pady=20, padx=20, fill="both", expand=True)

            # Create table header
            header_frame = ctk.CTkFrame(self.table_frame)
            header_frame.pack(fill="x")
            for i, header in enumerate(headers):
                label = ctk.CTkLabel(header_frame, text=header, width=100, anchor="w")
                label.grid(row=0, column=i, padx=5)

            # Populate rows
            if data is not None:
                for row_index, row_data in enumerate(data):
                    self.create_table_row(row_data, row_index)

    def create_table_row(self, row_data, row_index):
        row_frame = ctk.CTkFrame(self.table_frame)
        row_frame.pack(fill="x", pady=2)

        # Display each column in the row
        if row_data is not None:
            for col_index, value in enumerate(row_data):
                label = ctk.CTkLabel(row_frame, text=value, width=100, anchor="w")
                label.grid(row=0, column=col_index, padx=5)

        # Select button
        select_button = ctk.CTkButton(row_frame, text="Select", width=70, 
                                      command=lambda: self.on_select(row_data))
        select_button.grid(row=0, column=len(row_data), padx=5)

    def on_select(self, row_data):
        # Call the callback with selected row data
        self.on_row_select(row_data)
        self.destroy()