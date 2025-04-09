# modules/data_converter.py

def convert_conanml_to_opendrop(user_input_data, pendant_features):
    """
    Convert ConanML ExperimentalSetup and PendantFeatures into OpenDrop-compatible dictionary.
    """
    return {
        "drop_points": pendant_features.drop_points,
        "drop_apex": pendant_features.drop_apex,
        "drop_radius": pendant_features.drop_radius,
        "drop_rotation": pendant_features.drop_rotation,
        "needle_diameter": pendant_features.needle_diameter,
        "density_outer": user_input_data.density_outer,
        "density_drop": user_input_data.user_input_fields.get("drop_density"),
        "pixel_to_mm": user_input_data.user_input_fields.get("pixel_mm"),
        "params": user_input_data.fitted_params,
    }
