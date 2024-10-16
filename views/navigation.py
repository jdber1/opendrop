# navigation.py
from customtkinter import *

def create_navigation(parent):
    # Create a frame for the navigation
    navigation_frame = CTkFrame(parent)
    navigation_frame.pack(pady=10, padx=10, fill='x')

    # Define stage labels for navigation
    stages = ["Preparation", "Acquisition", "Analysis", "Output"]

    # Create a canvas for the progress bar
    canvas = CTkCanvas(navigation_frame, height=50)
    canvas.pack(fill='x', expand=True)

    current_stage = 0  # Track the current stage

    # Function to update the progress bar and adjust to the parent width
    def update_progress(stage_index):
        nonlocal current_stage
        if 0 <= stage_index < len(stages):
            # Get the current width of the canvas (parent container width)
            canvas_width = canvas.winfo_width()

            # Calculate 80% of the canvas width and center it
            progress_width = int(0.8 * canvas_width)  # 80% of canvas width
            left_x = (canvas_width - progress_width) // 2  # Center the bar
            right_x = left_x + progress_width

            # Update the background bar
            canvas.coords(progress_bar_bg, left_x, 20, right_x, 30)

            # Calculate the width for the progress bar based on the current stage
            filled_width = left_x + (stage_index * (progress_width // (len(stages) - 1)))
            canvas.coords(progress_bar, left_x, 20, filled_width, 30)

            # Update label positions dynamically
            for i, label in enumerate(stage_labels):
                label_x = left_x + (i * (progress_width // (len(stages) - 1)))
                canvas.coords(label, label_x, 15)

            # Update current stage
            current_stage = stage_index

    # Define next and prev functions to control the stage
    def next_stage():
        if current_stage < len(stages) - 1:
            update_progress(current_stage + 1)

    def prev_stage():
        if current_stage > 0:
            update_progress(current_stage - 1)

    # Resize the progress bar and labels when the window is resized
    def on_resize(event):
        update_progress(current_stage)

    # Bind the resize event to dynamically adjust the progress bar and labels
    canvas.bind("<Configure>", on_resize)

    # Create the progress bar background (initial size, dynamically resized later)
    progress_bar_bg = canvas.create_rectangle(10, 20, 390, 30, fill='lightgrey')

    # Create the progress bar itself (initial size, dynamically resized later)
    progress_bar = canvas.create_rectangle(10, 20, 10, 30, fill='blue')

    # Create stage labels at quarter positions
    stage_labels = []
    for i, stage in enumerate(stages):
        label = canvas.create_text(10, 15, text=stage, anchor='center', font=("Helvetica", 8))
        stage_labels.append(label)

    # Return the control functions
    return next_stage, prev_stage

# Main application window
if __name__ == "__main__":
    app = CTk()
    app.title("Responsive Progress Bar Example")
    app.geometry("600x150")

    next_stage, prev_stage = create_navigation(app)

    # Example usage of next and prev functions (can be connected to buttons)
    next_stage()  # Move to the next stage
    prev_stage()  # Move to the previous stage

    app.mainloop()
