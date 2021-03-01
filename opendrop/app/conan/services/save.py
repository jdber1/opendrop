# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


import copy
import csv
import math
from pathlib import Path
from typing import Optional, Sequence, Tuple, NamedTuple

from injector import inject
import numpy as np
import PIL.Image

from opendrop.utility.bindable import VariableBindable
from opendrop.utility.misc import clear_directory_contents
from opendrop.app.common.analysis_saver.figure_options import FigureOptions
from opendrop.app.common.analysis_saver.misc import simple_grapher
from opendrop.app.conan.services.analysis import ConanAnalysisJob


class ConanSaveParams(NamedTuple):
    root_dir: Path
    ca_plot_options: FigureOptions


class ConanSaveParamsFactory:
    def __init__(self) -> None:
        self.bn_save_dir_parent = VariableBindable(None)
        self.bn_save_dir_name = VariableBindable('')

        self.angle_figure_opts = FigureOptions(
            should_save=True,
            dpi=300,
            size_w=15,
            size_h=9
        )

    @property
    def save_root_dir(self) -> Path:
        return self.bn_save_dir_parent.get() / self.bn_save_dir_name.get()

    def create(self) -> ConanSaveParams:
        parent_dir = self.bn_save_dir_parent.get()
        assert parent_dir is not None

        name = self.bn_save_dir_name.get()
        assert name

        root_dir = parent_dir / name

        return ConanSaveParams(
            root_dir,
            copy.deepcopy(self.angle_figure_opts),
        )


class ConanSaveService:
    @inject
    def __init__(self, default_params_factory: ConanSaveParamsFactory):
        self._default_params_factory = default_params_factory

    def save(self, jobs: Sequence[ConanAnalysisJob], params: Optional[ConanSaveParams] = None) -> None:
        params = params or self._default_params_factory.create()

        root_dir = params.root_dir
        assert root_dir.is_dir() or not root_dir.exists()
        root_dir.mkdir(parents=True, exist_ok=True)
        clear_directory_contents(root_dir)

        padding = len(str(len(jobs)))
        for i, drop in enumerate(jobs):
            job_dir = root_dir/(root_dir.name + f"{i+1:0>{padding}}")
            _save_individual(drop, job_dir)

        with (root_dir/'timeline.csv').open('w', newline='') as out_file:
            _save_timeline(jobs, out_file)

        if len(jobs) <= 1:
            return

        figure_opts = params.ca_plot_options
        if figure_opts.bn_should_save.get():
            fig_size = figure_opts.size
            dpi = figure_opts.bn_dpi.get()
            with (root_dir/'left_angle_plot.png').open('wb') as out_file:
                _save_left_angle_plot(
                    jobs,
                    out_file=out_file,
                    fig_size=fig_size,
                    dpi=dpi,
                )
            with (root_dir/'right_angle_plot.png').open('wb') as out_file:
                _save_right_angle_plot(
                    jobs,
                    out_file=out_file,
                    fig_size=fig_size,
                    dpi=dpi,
                )


def _save_individual(drop: ConanAnalysisJob, dir_path: Path) -> None:
    dir_path.mkdir(parents=True)

    _save_image(drop, out_file_path=dir_path/'image.png')

    with (dir_path/'drop_points.csv').open('wb') as out_file:
        _save_drop_points(drop, out_file=out_file)


def _save_image(job: ConanAnalysisJob, out_file_path: Path) -> None:
    if job.image is None:
        return

    if job.image_replicated:
        # A copy of the image already exists somewhere, we don't need to save it again.
        return

    image = PIL.Image.fromarray(job.image)
    image.save(out_file_path)


def _save_drop_points(drop: ConanAnalysisJob, out_file) -> None:
    drop_points = drop.drop_points
    if drop_points is None or drop_points.shape[1] == 0:
        return

    np.savetxt(out_file, drop_points.T, fmt='%.1f,%.1f')


def _save_left_angle_plot(
        jobs: Sequence[ConanAnalysisJob],
        out_file,
        fig_size: Tuple[float, float],
        dpi: int,
) -> None:
    jobs = [ job for job in jobs
             if job.timestamp is not None and job.left_angle is not None ]

    fig = simple_grapher(
        'Time [s]',
        'Left CA [°]',
        [job.timestamp for job in jobs],
        [math.degrees(job.left_angle) for job in jobs],
        marker='.',
        line_style='-',
        color='blue',
        fig_size=fig_size,
        dpi=dpi
    )

    fig.savefig(out_file)


def _save_right_angle_plot(
        jobs: Sequence[ConanAnalysisJob],
        out_file,
        fig_size: Tuple[float, float],
        dpi: int,
) -> None:
    jobs = [ job for job in jobs
             if job.timestamp is not None and job.right_angle is not None ]

    fig = simple_grapher(
        'Time [s]',
        'Right CA [°]',
        [job.timestamp for job in jobs],
        [math.degrees(job.right_angle) for job in jobs],
        marker='.',
        line_style='-',
        color='blue',
        fig_size=fig_size,
        dpi=dpi
    )

    fig.savefig(out_file)


def _save_timeline(jobs: Sequence[ConanAnalysisJob], out_file) -> None:
    writer = csv.writer(out_file)
    writer.writerow([
        'Time [s]',
        'Left CA [deg.]',
        'Right CA [deg.]',
        'Left Pt x [px]',
        'Left Pt y [px]',
        'Right Pt x [px]',
        'Right Pt y [px]',
    ])

    for job in jobs:
        timestamp = job.timestamp
        left_angle = job.left_angle
        left_contact = job.left_contact
        right_angle = job.right_angle
        right_contact = job.right_contact

        writer.writerow([
            format(timestamp, '.1f') if timestamp is not None else '',
            format(math.degrees(left_angle), '.1f') if left_angle is not None else '',
            format(math.degrees(right_angle), '.1f') if right_angle is not None else '',
            format(left_contact.x, '.1f') if left_contact is not None else '',
            format(left_contact.y, '.1f') if left_contact is not None else '',
            format(right_contact.x, '.1f') if right_contact is not None else '',
            format(right_contact.y, '.1f') if right_contact is not None else '',
        ])
