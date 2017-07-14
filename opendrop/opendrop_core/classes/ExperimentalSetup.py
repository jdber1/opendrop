from opendrop.utility.structs import Struct

class ExperimentalSetup(Struct):
    attributes = (
        "screen_resolution",
        "drop_density",
        "continuous_density",
        "needle_diameter_mm",
        "residuals_boole",
        "profiles_boole",
        "interfacial_tension_boole",
        "image_source",
        "number_of_frames",
        "wait_time",
        "save_images_boole",
        "create_folder_boole",
        "filename",
        "directory_string",
        "time_string",
        "local_files",
        "threshold_val",
        "drop_region",
        "needle_region",
        "auto_test_parameters",
        "conAn_type"
    )

    default = None
