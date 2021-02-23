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


import configparser
import csv
import math
from collections import OrderedDict
from pathlib import Path
from typing import Sequence, Tuple, Iterable

import cv2
import numpy as np

from opendrop.app.common.analysis_saver.misc import simple_grapher
from opendrop.app.ift.services.analysis import PendantAnalysisJob
from opendrop.utility.misc import clear_directory_contents
from .model import IFTAnalysisSaverOptions


def save_drops(drops: Iterable[PendantAnalysisJob], options: IFTAnalysisSaverOptions) -> None:
    drops = list(drops)

    full_dir = options.save_root_dir
    assert full_dir.is_dir() or not full_dir.exists()
    full_dir.mkdir(parents=True, exist_ok=True)
    clear_directory_contents(full_dir)

    padding = len(str(len(drops)))
    dir_name = options.bn_save_dir_name.get()
    for i, drop in enumerate(drops):
        drop_dir_name = dir_name + '{n:0>{padding}}'.format(n=(i+1), padding=padding)  # i+1 for 1-based indexing.
        _save_individual(drop, drop_dir_name, options)

    with (full_dir/'timeline.csv').open('w', newline='') as out_file:
        _save_timeline_data(drops, out_file)

    if len(drops) <= 1:
        return

    figure_opts = options.ift_figure_opts
    if figure_opts.bn_should_save.get():
        fig_size = figure_opts.size
        dpi = figure_opts.bn_dpi.get()
        with (full_dir/'ift_plot.png').open('wb') as out_file:
            _save_ift_figure(
                drops=drops,
                out_file=out_file,
                fig_size=fig_size,
                dpi=dpi)

    figure_opts = options.volume_figure_opts
    if figure_opts.bn_should_save.get():
        fig_size = figure_opts.size
        dpi = figure_opts.bn_dpi.get()
        with (full_dir/'volume_plot.png').open('wb') as out_file:
            _save_volume_figure(
                drops=drops,
                out_file=out_file,
                fig_size=fig_size,
                dpi=dpi)

    figure_opts = options.surface_area_figure_opts
    if figure_opts.bn_should_save.get():
        fig_size = figure_opts.size
        dpi = figure_opts.bn_dpi.get()
        with (full_dir/'surface_area_plot.png').open('wb') as out_file:
            _save_surface_area_figure(
                drops=drops,
                out_file=out_file,
                fig_size=fig_size,
                dpi=dpi)


def _save_individual(drop: PendantAnalysisJob, drop_dir_name: str, options: IFTAnalysisSaverOptions) -> None:
    full_dir = options.save_root_dir/drop_dir_name
    full_dir.mkdir(parents=True)

    _save_drop_image(drop, out_file_path=full_dir / 'image.png')

    with (full_dir/'params.ini').open('w') as out_file:
        _save_drop_params(drop, out_file=out_file)

    with (full_dir/'extracted.csv').open('wb') as out_file:
        _save_drop_contour(drop, out_file=out_file)

    with (full_dir/'fit.csv').open('wb') as out_file:
        _save_drop_contour_fit(drop, out_file=out_file)

    with (full_dir/'residuals.csv').open('wb') as out_file:
        _save_drop_contour_fit_residuals(drop, out_file=out_file)

    drop_residuals_figure_opts = options.drop_residuals_figure_opts
    if drop_residuals_figure_opts.bn_should_save.get():
        fig_size = drop_residuals_figure_opts.size
        dpi = drop_residuals_figure_opts.bn_dpi.get()
        with (full_dir/'residuals_plot.png').open('wb') as out_file:
            _save_drop_contour_fit_residuals_figure(
                drop=drop,
                out_file=out_file,
                fig_size=fig_size,
                dpi=dpi)


def _save_drop_image(drop: PendantAnalysisJob, out_file_path: Path) -> None:
    if drop.is_image_replicated:
        # A copy of the image already exists somewhere, we don't need to save it again.
        return

    image = drop.bn_image.get()
    if image is None:
        return

    cv2.imwrite(str(out_file_path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def _save_drop_params(drop: PendantAnalysisJob, out_file) -> None:
    root = configparser.ConfigParser(allow_no_value=True)
    root.read_dict(OrderedDict((
        ('Physical', OrderedDict((
            ('; all quantities are in SI units', None),
            ('timestamp', format(drop.bn_image_timestamp.get(), '.3g')),
            ('interfacial_tension', format(drop.bn_interfacial_tension.get(), '.3g')),
            ('volume', format(drop.bn_volume.get(), '.3g')),
            ('surface_area', format(drop.bn_surface_area.get(), '.3g')),
            ('apex_radius', format(drop.bn_apex_radius.get(), '.3g')),
            ('worthington', format(drop.bn_worthington.get(), '.3g')),
            ('bond_number', format(drop.bn_bond_number.get(), '.3g')),
        ))),
        ('Image', OrderedDict((
            ('; regions are defined by (left, top, right, bottom) tuples', None),
            ('drop_region', tuple(drop.bn_drop_region.get())),
            ('needle_region', tuple(drop.bn_needle_region.get())),
            ('apex_coordinates', '({0.x:.1f}, {0.y:.1f})'.format(drop.bn_apex_coords_px.get())),
            ('; needle width in pixels', None),
            ('needle_width', format(drop.bn_needle_width_px.get(), '.3g')),
            ('; angle is in degrees (positive is counter-clockwise)', None),
            ('image_angle', format(math.degrees(drop.bn_rotation.get()), '.3g')),
        ))),
    )))

    root.write(out_file)


def _save_drop_contour(drop: PendantAnalysisJob, out_file) -> None:
    drop_profile_extract = drop.bn_drop_profile_extract.get()
    if drop_profile_extract is None:
        return

    np.savetxt(out_file, drop_profile_extract, fmt='%.1f,%.1f')


def _save_drop_contour_fit(drop: PendantAnalysisJob, out_file) -> None:
    drop_contour_fit = drop.bn_drop_profile_fit.get()
    if drop_contour_fit is None:
        return

    np.savetxt(out_file, drop_contour_fit, fmt='%.1f,%.1f')


def _save_drop_contour_fit_residuals(drop: PendantAnalysisJob, out_file) -> None:
    arclengths = drop.bn_arclengths.get()
    residuals = drop.bn_residuals.get()
    if arclengths is None or residuals is None:
        return

    np.savetxt(out_file, np.array([arclengths, residuals]).T, fmt='%g,%g')


def _save_drop_contour_fit_residuals_figure(drop: PendantAnalysisJob, out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    arclengths = drop.bn_arclengths.get()
    residuals = drop.bn_residuals.get()
    if arclengths is None or residuals is None:
        return

    fig = simple_grapher(
        label_x=r'Arclength',
        label_y='Residual',
        data_x=arclengths,
        data_y=residuals,
        color='blue',
        marker='.',
        line_style='',
        fig_size=fig_size,
        dpi=dpi)

    fig.savefig(out_file)


def _save_ift_figure(drops: Sequence[PendantAnalysisJob], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [
        drop
        for drop in drops
        if math.isfinite(drop.bn_image_timestamp.get()) and
           math.isfinite(drop.bn_interfacial_tension.get())
    ]

    start_time = min(drop.bn_image_timestamp.get() for drop in drops)
    data = (
        (
            drop.bn_image_timestamp.get() - start_time,
            drop.bn_interfacial_tension.get() * 1e3
        )
        for drop in drops
    )

    fig = simple_grapher(
        'Time [s]',
        'Interfacial tension [mN m⁻¹]',
        *zip(*data),
        marker='.',
        line_style='-',
        color='red',
        fig_size=fig_size,
        dpi=dpi)

    fig.savefig(out_file)


def _save_volume_figure(drops: Sequence[PendantAnalysisJob], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [
        drop
        for drop in drops
        if math.isfinite(drop.bn_image_timestamp.get()) and
           math.isfinite(drop.bn_volume.get())
    ]

    start_time = min(drop.bn_image_timestamp.get() for drop in drops)
    data = (
        (
            drop.bn_image_timestamp.get() - start_time,
            drop.bn_volume.get() * 1e9
        )
        for drop in drops
    )

    fig = simple_grapher(
        'Time [s]',
        'Volume [mm³]',
        *zip(*data),
        marker='.',
        line_style='-',
        color='blue',
        fig_size=fig_size,
        dpi=dpi)

    fig.savefig(out_file)


def _save_surface_area_figure(drops: Sequence[PendantAnalysisJob], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [
        drop
        for drop in drops
        if math.isfinite(drop.bn_image_timestamp.get()) and
           math.isfinite(drop.bn_surface_area.get())
    ]

    start_time = min(drop.bn_image_timestamp.get() for drop in drops)
    data = (
        (
            drop.bn_image_timestamp.get() - start_time,
            drop.bn_surface_area.get() * 1e6
        )
        for drop in drops
    )

    fig = simple_grapher(
        'Time [s]',
        'Surface area [mm²]',
        *zip(*data),
        marker='.',
        line_style='-',
        color='green',
        fig_size=fig_size,
        dpi=dpi
    )

    fig.savefig(out_file)


def _save_timeline_data(drops: Sequence[PendantAnalysisJob], out_file) -> None:
    writer = csv.writer(out_file)
    writer.writerow([
        'Time [s]',
        'IFT [N/m]',
        'Volume [m3]',
        'Surface [m2]',
        'Radius [m]',
        'Worth.',
        'Bond',
        'Rotation [deg.]',
        'Apex x [px]',
        'Apex y [px]',
        'Needle width [px]',
    ])

    for drop in drops:
        writer.writerow([
            format(drop.bn_image_timestamp.get(), '.1f'),
            format(drop.bn_interfacial_tension.get(), '.3g'),
            format(drop.bn_volume.get(), '.3g'),
            format(drop.bn_surface_area.get(), '.3g'),
            format(drop.bn_apex_radius.get(), '.3g'),
            format(drop.bn_worthington.get(), '.3g'),
            format(drop.bn_bond_number.get(), '.3g'),
            format(math.degrees(drop.bn_rotation.get()), '.3g'),
            format(drop.bn_apex_coords_px.get()[0], '.1f'),
            format(drop.bn_apex_coords_px.get()[1], '.1f'),
            format(drop.bn_needle_width_px.get(), '.1f'),
        ])
