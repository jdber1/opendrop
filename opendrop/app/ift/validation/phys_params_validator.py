from opendrop.app.ift.analysis_model.phys_params import IFTPhysicalParametersFactory


class IFTPhysicalParametersFactoryValidator:
    def __init__(self, target: IFTPhysicalParametersFactory) -> None:
        self._target = target

    @property
    def is_valid(self) -> bool:
        try:
            self._target.create_physical_parameters()
        except ValueError:
            return False

        return True
