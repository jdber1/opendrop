# dynamic_content.py
from customtkinter import *

def create_dynamic_content(content_frame):
    # Left side for user inputs
    left_frame = CTkFrame(content_frame)
    left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    input_labels = [
        "Drop Region:", "Needle Region:", "Drop Density:", 
        "Needle Diameter:", "Continuous density (kg/m³):", "Pixel to mm Ratio:"
    ]

    for i, label_text in enumerate(input_labels):
        label = CTkLabel(left_frame, text=label_text)
        label.grid(row=i, column=0, sticky="e", padx=10, pady=5)
        
        if "Region" in label_text:
            entry = CTkButton(left_frame, text="Select")  # Simulating region selection buttons
        else:
            entry = CTkEntry(left_frame)  # Normal input fields
        entry.grid(row=i, column=1, padx=10, pady=5)

    # Checkbox for "Residuals"
    residuals_frame = CTkFrame(content_frame)
    residuals_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
    residuals_checkbox = CTkCheckBox(residuals_frame, text="Residuals")
    residuals_checkbox.grid(row=0, column=0)

    # Right side for analysis methods
    right_frame = CTkFrame(content_frame)
    right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    analysis_label = CTkLabel(right_frame, text="Analysis Methods")
    analysis_label.pack(pady=10)

    default_checkbox = CTkCheckBox(right_frame, text="Default")
    default_checkbox.pack()
