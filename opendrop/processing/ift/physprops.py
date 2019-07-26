import numpy as np


# Quantities are in SI units
def calculate_ift(
        inner_density: float,
        outer_density: float,
        bond_number: float,
        apex_radius: float,
        gravity: float
) -> float:
    delta_density = abs(inner_density - outer_density)
    gamma_ift = delta_density * gravity * apex_radius ** 2 / bond_number

    return gamma_ift


# Quantities are in SI units
def calculate_worthington(
        inner_density: float,
        outer_density: float,
        gravity: float,
        ift: float,
        volume: float,
        needle_width: float
) -> float:
    delta_density = abs(inner_density - outer_density)
    worthington_number = (delta_density * gravity * volume) / (np.pi * ift * needle_width)

    return worthington_number
