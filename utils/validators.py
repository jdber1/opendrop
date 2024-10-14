# Function to validate numeric input
def validate_numeric_input(value):
    # Allows empty string or only numeric values
    return value.isdigit() or value == ""

def validate_int(action, index, value_if_allowed,
                     prior_value, text, validation_type, trigger_type, widget_name):  
    if value_if_allowed == '':
        # self.recheck_wait_state(0)
        return True
    elif value_if_allowed == '0':
        return False
    else:
        if text in '0123456789':
            try:
                int_value = int(value_if_allowed)
                # self.recheck_wait_state(int_value)
                return True
            except ValueError:
                return False
        else:
            return False
        
def validate_float(action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):
    if value_if_allowed == '':
        return True
    elif value_if_allowed == '.':
        return True
    else:
        if text in '0123456789.-+':
            try:
                float(value_if_allowed)
                return True
            except ValueError:
                return False
        else:
            return False
