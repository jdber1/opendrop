from typing import Optional

from opendrop.iftcalc.analyser import IFTAnalysis, IFTDropAnalysis
from opendrop.utility.bindable.bindable import ListBindable, MutableSequenceBindable


class IFTResultsExplorer:
    class SummaryData:
        pass

    def __init__(self):
        self._analysis = None
        self.individual_drops = ListBindable()  # type: MutableSequenceBindable[IFTDropAnalysis]
        self.summary_data = None  # type: Optional[IFTResultsExplorer.SummaryData]

    analysis = property()

    @analysis.setter
    def analysis(self, analysis: IFTAnalysis) -> None:
        self._analysis = analysis

        self.individual_drops.clear()
        for drop in self._analysis.drops:
            self.individual_drops.insert(0, drop)
