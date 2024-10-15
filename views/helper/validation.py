def validate_user_input_data_ift(user_input_data):
        """Validate the user input data and return messages for missing fields."""
        messages = []

        user_input_fields = user_input_data.user_input_fields
            # Ensure if drop region is chosen, it must not be None
        if user_input_fields['drop_region_choice'] != 'Automated' and user_input_data.ift_drop_region is None:
            messages.append("Please select drop region")

        # Ensure if needle region is chosen, it must not be None
        if user_input_fields['needle_region_choice'] != 'Automated' and user_input_data.ift_needle_region is None:
            messages.append("Please select needle region")

            # Check user_input_fields for None values
        
        required_fields = {
            'drop_region_choice': "Drop Region Choice",
            'needle_region_choice': "Needle Region Choice",
            'drop_density': "Drop Density",
            'needle_diameter': "Needle Diameter",
            'continuous_density': "Continuous Density",
            'pixel_mm': "Pixel to mm"
        }

        for field, label in required_fields.items():
            if user_input_fields.get(field) is None:
                messages.append(f"{label} is required")

        # Check if analysis_method_fields has at least one method selected
        analysis_method_fields = user_input_data.analysis_method_fields
        if not any(analysis_method_fields.values()):
            messages.append("At least one analysis method must be selected.")

        return messages

def validate_user_input_data_cm(user_input_data):
    """Validate the user input data and return messages for missing fields."""
    messages = []
    print("validate_user_input_data_cm")
    user_input_fields = user_input_data.user_input_fields_cm
        # Ensure if drop region is chosen, it must not be None
    if user_input_fields['drop_id_method'] != 'Automated' and user_input_data.ift_drop_region is None:
        messages.append("Please select drop_id_method")

    # Ensure if needle region is chosen, it must not be None
    if user_input_fields['threshold_method'] != 'Automated' and user_input_data.ift_needle_region is None:
        messages.append("Please select threshold_method")

    if user_input_fields['baseline_method'] != 'Automated' and user_input_data.ift_needle_region is None:
        messages.append("Please select baseline_method")

    
    required_fields = {
        'threshold_value': "Threshold Value",
        'density_outer': "Density Outer",
        'needle_diameter': "Needle Diameter"
    }

    for field, label in required_fields.items():
        if user_input_fields.get(field) is None:
            messages.append(f"{label} is required")

    # Check if analysis_method_fields has at least one method selected
    analysis_method_fields = user_input_data.analysis_method_fields_cm
    if not any(analysis_method_fields.values()):
        messages.append("At least one analysis method must be selected.")

    return messages
