# Function to validate numeric input
def validate_numeric_input(value):
    # Allows empty string or only numeric values
    return value.isdigit() or value == ""
