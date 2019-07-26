from typing import Sequence, Optional

from opendrop.app.conan.analysis import ConanAnalysis
from opendrop.utility.bindable import Bindable


class IndividualModel:
    def __init__(
            self,
            in_analyses: Bindable[Sequence[ConanAnalysis]],
            bind_selection: Bindable[Optional[ConanAnalysis]]
    ) -> None:
        self.bn_analyses = in_analyses
        self.bn_selection = bind_selection
