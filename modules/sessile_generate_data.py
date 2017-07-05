import basic_generate_data
import numpy as np

GRAVITY = 9.80035 # gravitational acceleration in Melbourne, Australia

pi = np.pi


class SessileGenerateData(basic_generate_data.BasicGenerateData):

    def calculate_Wo(self, fitted_drop_data, user_inputs,ift_mN,vol_uL):
        Delta_rho = -(user_inputs.drop_density - user_inputs.continuous_density)
        needle_diameter = user_inputs.needle_diameter_mm
        Wo =  Delta_rho * GRAVITY * vol_uL*1e-9/(pi*ift_mN*1e-3*needle_diameter*1e-3)
        return Wo