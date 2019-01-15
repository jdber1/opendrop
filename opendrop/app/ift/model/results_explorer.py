from operator import attrgetter
from typing import Optional, Sequence

from opendrop.app.ift.model.analyser import IFTAnalysis, IFTDropAnalysis
from opendrop.utility.bindable.bindable import AtomicBindable, AtomicBindableVar


class IFTResultsExplorer:
    class SummaryData:
        pass

    def __init__(self):
        self._analysis = None
        self.bn_individual_drops = AtomicBindableVar(tuple())  # type: AtomicBindable[Sequence[IFTDropAnalysis]]
        self.bn_summary_data = AtomicBindableVar(None)  # type: AtomicBindable[Optional[IFTResultsExplorer.SummaryData]]

    individual_drops = AtomicBindable.property_adapter(attrgetter('bn_individual_drops'))
    summary_data = AtomicBindable.property_adapter(attrgetter('bn_summary_data'))

    analysis = property()

    @analysis.setter
    def analysis(self, analysis: IFTAnalysis) -> None:
        self._analysis = analysis
        self.bn_individual_drops.set(tuple(self._analysis.drops))
