from customtkinter import *

def create_navigation(parent):
    # Create a frame for the navigation
    navigation_frame = CTkFrame(parent)
    
    # Define stage labels for navigation
    stages = ["Acquisition", "Preparation", "Analysis", "Output"]
    
    # Create a label for each stage
    for index, stage in enumerate(stages):
        # Create a label for each stage
        stage_label = CTkLabel(navigation_frame, text=stage, text_color="black")
        stage_label.grid(row=0, column=index, padx=20, pady=10, sticky="nsew")
        
        # Create a dot to indicate the current stage
        dot = CTkCanvas(navigation_frame, width=10, height=10, bg="white", highlightthickness=0)
        dot.grid(row=1, column=index, padx=10)
        dot.create_oval(2, 2, 8, 8, fill="black")  # Draw the dot
        
        # Make stage label responsive
        navigation_frame.grid_columnconfigure(index, weight=1)

    # Return the navigation frame
    return navigation_frame