# frame_interval
def validate_frame_interval(user_input_data):
    print(user_input_data.import_files)
    if len(user_input_data.import_files) > 1:
        if user_input_data.frame_interval is None:
            return False
    return True

def validate_user_input_data_ift(user_input_data):
        """Validate the user input data and return messages for missing fields."""
        messages = []

            # Ensure if drop region is chosen, it must not be None
        if user_input_data.drop_ID_method != 'Automated' and user_input_data.ift_drop_region is None:
            messages.append("Please select drop region")

        # Ensure if needle region is chosen, it must not be None
        if user_input_data.needle_region_choice != 'Automated' and user_input_data.ift_needle_region is None:
            messages.append("Please select needle region")

            # Check user_input_fields for None values
        
        required_fields = {
            'drop_density': "Drop Density",
            'density_outer': "Continuous Density",
            'needle_diameter_mm': "Needle Diameter",
            'pixel_mm': "Pixel to mm"
        }

        for field, label in required_fields.items():
            value = getattr(user_input_data, field, None)  # Get the attribute or None if missing
            print(field," is ",value)
            if value is None or value == "" or value ==0.0:  # Check for both None and empty string
                messages.append(f"{label} is required")


        # Check if analysis_method_fields has at least one method selected
        if not any(user_input_data.analysis_methods_pd.values()):
            messages.append("At least one analysis method must be selected.")

        return messages

def validate_user_input_data_cm(user_input_data,experimental_drop):
    """Validate the user input data and return messages for missing fields."""
    messages = []

    """
        # Ensure if drop region is chosen, it must not be None
    if user_input_data.drop_ID_method != 'Automated' and user_input_data.edgefinder is None:
        messages.append("Please select drop_id_method")

    # Ensure if needle region is chosen, it must not be None
    if user_input_data.threshold_method != 'Automated' and user_input_data.edgefinder is None:
        messages.append("Please select threshold_method")

    if user_input_data.baseline_method != 'Automated' and user_input_data.edgefinder is None:
        messages.append("Please select baseline_method")

    """
        # Ensure if drop region is chosen, it must not be None
    if user_input_data.drop_ID_method != 'Automated' and experimental_drop.cropped_image is None:
        messages.append("Please select drop region")

    # Ensure if needle region is chosen, it must not be None
    if user_input_data.baseline_method != 'Automated' and experimental_drop.drop_contour is None:
        messages.append("Please select baseline region")

        # Check user_input_fields for None values
    if user_input_data.baseline_method != 'Automated' and user_input_data.threshold_val is None:
        messages.append("Please enter threshold value")

    required_fields = {
        'threshold_method':"Threshold Value",
        'density_outer': "Continuous Density",
        'needle_diameter_mm': "Needle Diameter",
    }

    if not any(user_input_data.analysis_methods_ca.values()):
            messages.append("At least one analysis method must be selected.")

    for field, label in required_fields.items():
        value = getattr(user_input_data, field, None)  # Get the attribute or None if missing
        if value is None or value == "":  # Check for both None and empty string
            messages.append(f"{label} is required")
    
    # Check if analysis_method_fields has at least one method selected
    if not any(user_input_data.analysis_methods_pd.values()):
        messages.append("At least one analysis method must be selected.")

    return messages
    
