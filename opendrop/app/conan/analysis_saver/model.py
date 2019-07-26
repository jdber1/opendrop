from pathlib import Path
from typing import Optional

from opendrop.app.common.analysis_saver.figure_options import FigureOptions
from opendrop.utility.bindable import Bindable, BoxBindable


class ConanAnalysisSaverOptions:
    def __init__(self) -> None:
        self.bn_save_dir_parent = BoxBindable(None)  # type: Bindable[Optional[Path]]
        self.bn_save_dir_name = BoxBindable('')

        self.angle_figure_opts = FigureOptions(
            should_save=True,
            dpi=300,
            size_w=15,
            size_h=9
        )

    @property
    def save_root_dir(self) -> Path:
        return self.bn_save_dir_parent.get() / self.bn_save_dir_name.get()
