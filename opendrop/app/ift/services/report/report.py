from opendrop.utility.bindable import VariableBindable


class IFTReportService:
    def __init__(self) -> None:
        self.bn_analyses = VariableBindable(tuple())
