from opendrop.app.ift.analysis.physical_properties import PhysicalPropertiesCalculatorParams


class PhysicalParametersModel:
    def __init__(self, physprops_calculator_params: PhysicalPropertiesCalculatorParams) -> None:
        self._params = physprops_calculator_params

        self.bn_inner_density = physprops_calculator_params.bn_inner_density
        self.bn_outer_density = physprops_calculator_params.bn_outer_density
        self.bn_needle_width = physprops_calculator_params.bn_needle_width
        self.bn_gravity = physprops_calculator_params.bn_gravity
