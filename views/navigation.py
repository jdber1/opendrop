from customtkinter import *

def create_navigation(parent):
    # Create a frame for the navigation
    navigation_frame = CTkFrame(parent)
    navigation_frame.pack(pady=10, padx=10, fill='x')

    # Define stage labels for navigation
    stages = ["Preparation", "Acquisition", "Analysis", "Output"]

    progress_bar = CTkProgressBar(navigation_frame)
    progress_bar.pack(fill='x', expand=True, padx=130, pady=(20,10))

    progress_bar.set(0)

    current_stage = 0  # Track the current stage

    # Function to update the progress bar and adjust to the parent width
    def update_progress(stage_index):
        nonlocal current_stage
        if 0 <= stage_index < len(stages):
            progress_bar.set(stage_index / (len(stages)-1))
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
    navigation_frame.bind("<Configure>", on_resize)

    # Create stage labels at quarter positions
    stage_labels = []
    for i, stage in enumerate(stages):
        # Create a label for each stage
        label = CTkLabel(navigation_frame, text=stage, font=("Roboto", 13), anchor='e')
        label.pack(side='left', expand=True)
        stage_labels.append(label)

    # Return the control functions
    return next_stage, prev_stage

# Main application window
if __name__ == "__main__":
    app = CTk()
    app.title("Progress Bar")
    app.geometry("600x150")

    next_stage, prev_stage = create_navigation(app)

    # Example usage of next and prev functions (can be connected to buttons)
    next_stage()  # Move to the next stage
    prev_stage()  # Move to the previous stage

    app.mainloop()
