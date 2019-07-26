from typing import Sequence, Optional

from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.utility.bindable import Bindable


class IndividualModel:
    def __init__(
            self,
            in_analyses: Bindable[Sequence[IFTDropAnalysis]],
            bind_selection: Bindable[Optional[IFTDropAnalysis]]
    ) -> None:
        self.bn_analyses = in_analyses
        self.bn_selection = bind_selection
