import configparser
import itertools
import math
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Sequence, Tuple, Union, Iterable

import cv2
import numpy as np
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator

from opendrop.app.ift.model.analyser import IFTDropAnalysis
from opendrop.utility.bindable import SetBindable
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable
from opendrop.utility.misc import clear_directory_contents
from opendrop.utility.validation import validate, check_is_positive, check_is_not_empty


# Save options container

class IFTAnalysisSaverOptions:
    class FigureOptions:
        def __init__(self, should_save: bool, dpi: int, size_w: float, size_h: float) -> None:
            self.bn_should_save = AtomicBindableVar(should_save)
            self.bn_dpi = AtomicBindableVar(dpi)
            self.bn_size_w = AtomicBindableVar(size_w)
            self.bn_size_h = AtomicBindableVar(size_h)

            # Validation

            self.dpi_err = validate(
                value=self.bn_dpi,
                checks=(check_is_not_empty,
                        check_is_positive),
                enabled=self.bn_should_save)
            self.size_w_err = validate(
                value=self.bn_size_w,
                checks=(check_is_not_empty,
                        check_is_positive),
                enabled=self.bn_should_save)
            self.size_h_err = validate(
                value=self.bn_size_h,
                checks=(check_is_not_empty,
                        check_is_positive),
                enabled=self.bn_should_save)

            self.errors = SetBindable.union(self.dpi_err, self.size_w_err, self.size_h_err)

        @property
        def size(self) -> Tuple[float, float]:
            return self.bn_size_w.get(), self.bn_size_h.get()

    def __init__(self) -> None:
        self.bn_save_dir_parent = AtomicBindableVar(None)  # type: AtomicBindable[Optional[Path]]
        self.bn_save_dir_name = AtomicBindableVar('')  # type: AtomicBindable[str]

        self.drop_residuals_figure_opts = self.FigureOptions(
            should_save=True,
            dpi=300,
            size_w=10,
            size_h=10)
        self.ift_figure_opts = self.FigureOptions(
            should_save=True,
            dpi=300,
            size_w=15,
            size_h=9)
        self.volume_figure_opts = self.FigureOptions(
            should_save=True,
            dpi=300,
            size_w=15,
            size_h=9)
        self.surface_area_figure_opts = self.FigureOptions(
            should_save=True,
            dpi=300,
            size_w=15,
            size_h=9)

        # Validation:

        self.save_dir_parent_err = validate(
            value=self.bn_save_dir_parent,
            checks=(check_is_not_empty,))
        self.save_dir_name_err = validate(
            value=self.bn_save_dir_name,
            checks=(check_is_not_empty,))

        errors = [self.save_dir_parent_err, self.save_dir_name_err]

        for figure_opts in (self.drop_residuals_figure_opts, self.ift_figure_opts, self.volume_figure_opts,
                            self.surface_area_figure_opts):
            errors.append(figure_opts.errors)

        self._errors = SetBindable.union(*errors)

    @property
    def has_errors(self) -> bool:
        return bool(self._errors)

    @property
    def save_root_dir(self) -> Path:
        return self.bn_save_dir_parent.get() / self.bn_save_dir_name.get()


# Helper functions

INCHES_PER_CM = 0.393701


def simple_grapher(label_x: str, label_y: str, data_x: Sequence[float], data_y: Sequence[float], color: str,
                   marker: str, line_style: str, fig_size: Tuple[float, float], *,
                   tick_x_interval: Optional[float] = None,
                   xlim: Union[str, Tuple[float, float]] = 'tight',
                   grid: bool = True,
                   dpi: int = 300):
    fig_size_in = INCHES_PER_CM * fig_size[0], INCHES_PER_CM * fig_size[1]
    fig = Figure(figsize=fig_size_in, dpi=dpi)

    axes = fig.add_subplot(1, 1, 1)
    axes.plot(data_x, data_y, marker=marker, linestyle=line_style, color=color)

    if tick_x_interval is not None:
        axes.get_xaxis().set_major_locator(MultipleLocator(tick_x_interval))

    if xlim == 'tight':
        axes.set_xlim(min(data_x), max(data_x))
    else:
        axes.set_xlim(*xlim)

    axes.set_xlabel(label_x, fontname='sans-serif', fontsize=11)
    axes.set_ylabel(label_y, fontname='sans-serif', fontsize=11)
    for label in itertools.chain(axes.get_xticklabels(), axes.get_yticklabels()):
        label.set_fontsize(8)

    if grid:
        axes.grid(color='#dddddd')

    fig.tight_layout()

    return fig


# Main functions and classes start here

def _save_drop_image(drop: IFTDropAnalysis, out_file_path: Path) -> None:
    image = drop.image
    if image is None:
        return

    cv2.imwrite(str(out_file_path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def _save_drop_image_annotated(drop: IFTDropAnalysis, out_file_path: Path) -> None:
    image, image_annotations = drop.image, drop.image_annotations
    if image is None or image_annotations is None:
        return

    # Draw on a copy
    image = image.copy()

    # Draw extracted needle edges
    image = cv2.polylines(
        img=image,
        pts=image_annotations.needle_contours_px,
        isClosed=False,
        color=(0, 128, 255),
        thickness=1,
        lineType=cv2.LINE_AA)

    # Draw extracted drop profile
    image = cv2.polylines(
        img=image,
        pts=[image_annotations.drop_contour_px],
        isClosed=False,
        color=(0, 128, 255),
        thickness=1,
        lineType=cv2.LINE_AA)

    # Draw fitted drop profile
    drop_contour_fit = drop.generate_drop_contour_fit(samples=100)
    if drop_contour_fit is not None:
        drop_contour_fit += drop.apex_coords_px
        if np.isfinite(drop_contour_fit).all():
            drop_contour_fit = drop_contour_fit.astype(int)
            image = cv2.polylines(
                img=image,
                pts=[drop_contour_fit],
                isClosed=False,
                color=(255, 0, 128),
                thickness=1,
                lineType=cv2.LINE_AA)

    # Draw needle region
    image = cv2.rectangle(
        img=image,
        pt1=image_annotations.needle_region_px.p0,
        pt2=image_annotations.needle_region_px.p1,
        color=(13, 26, 255),
        thickness=1)

    # Draw drop region
    image = cv2.rectangle(
        img=image,
        pt1=image_annotations.drop_region_px.p0,
        pt2=image_annotations.drop_region_px.p1,
        color=(255, 26, 13),
        thickness=1)

    cv2.imwrite(str(out_file_path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def _save_drop_params(drop: IFTDropAnalysis, out_file) -> None:
    if drop.image_annotations is None:
        return

    root = configparser.ConfigParser(allow_no_value=True)
    root.read_dict(OrderedDict((
        ('Physical', OrderedDict((
            ('; all quantities are in SI units', None),
            ('timestamp', drop.image_timestamp),
            ('interfacial_tension', drop.interfacial_tension),
            ('volume', drop.volume),
            ('surface_area', drop.surface_area),
            ('apex_radius', drop.apex_radius),
            ('worthington', drop.worthington),
            ('bond_number', drop.bond_number),
        ))),
        ('Image', OrderedDict((
            ('; regions are defined by (left, top, right, bottom) tuples', None),
            ('drop_region', tuple(drop.image_annotations.drop_region_px)),
            ('needle_region', tuple(drop.image_annotations.needle_region_px)),
            ('apex_coordinates', drop.apex_coords_px),
            ('; needle width in pixels', None),
            ('needle_width', drop.phys_params.needle_width / drop.image_annotations.m_per_px),
            ('; angle is in degrees (positive is counter-clockwise)', None),
            ('image_angle', math.degrees(drop.apex_rot)),
        ))),
    )))

    root.write(out_file)


def _save_drop_contour(drop: IFTDropAnalysis, out_file) -> None:
    image_annotations = drop.image_annotations
    if image_annotations is None:
        return

    drop_contour = image_annotations.drop_contour_px
    np.savetxt(out_file, drop_contour, fmt='%d,%d')


def _save_drop_contour_fit(drop: IFTDropAnalysis, out_file, samples: int = 100) -> None:
    drop_contour_fit = drop.generate_drop_contour_fit(samples=samples)
    if drop_contour_fit is None:
        return

    # Translate (0, 0) to the drop apex coordinates of the image.
    drop_contour_fit += drop.apex_coords_px
    np.savetxt(out_file, drop_contour_fit, fmt='%d,%d')


def _save_drop_contour_fit_residuals(drop: IFTDropAnalysis, out_file) -> None:
    residuals = drop.drop_contour_fit_residuals
    if residuals is None:
        return

    np.savetxt(out_file, residuals, fmt='%g,%g')


def _save_drop_contour_fit_residuals_figure(drop: IFTDropAnalysis, out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    residuals = drop.drop_contour_fit_residuals
    if residuals is None:
        return

    max_x = max(4.5, max(residuals[:, 0]))

    fig = simple_grapher(
        label_x=r'Arclength $\bar{s}$',
        label_y='Residual',
        data_x=residuals[:, 0],
        data_y=residuals[:, 1],
        tick_x_interval=2,
        color='blue',
        marker='.',
        line_style='',
        fig_size=fig_size,
        xlim=(-max_x, max_x),
        dpi=dpi)

    fig.savefig(out_file)


def _save_ift_figure(drops: Sequence[IFTDropAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [drop for drop in drops if math.isfinite(drop.image_timestamp) and math.isfinite(drop.interfacial_tension)]
    start_time = min(drop.image_timestamp for drop in drops)
    data = ((drop.image_timestamp - start_time, drop.interfacial_tension*1e3) for drop in drops)

    fig = simple_grapher(
        'Time (s)',
        'Interfacial tension (mN m⁻¹)',
        *zip(*data),
        marker='.',
        line_style='-',
        color='red',
        fig_size=fig_size,
        dpi=dpi)

    fig.savefig(out_file)


def _save_volume_figure(drops: Sequence[IFTDropAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [drop for drop in drops if math.isfinite(drop.image_timestamp) and math.isfinite(drop.volume)]
    start_time = min(drop.image_timestamp for drop in drops)
    data = ((drop.image_timestamp - start_time, drop.volume*1e9) for drop in drops)

    fig = simple_grapher(
        'Time (s)',
        'Volume (mm³)',
        *zip(*data),
        marker='.',
        line_style='-',
        color='blue',
        fig_size=fig_size,
        dpi=dpi)

    fig.savefig(out_file)


def _save_surface_area_figure(drops: Sequence[IFTDropAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [drop for drop in drops if math.isfinite(drop.image_timestamp) and math.isfinite(drop.surface_area)]
    start_time = min(drop.image_timestamp for drop in drops)
    data = ((drop.image_timestamp - start_time, drop.surface_area*1e6) for drop in drops)

    fig = simple_grapher(
        'Time (s)',
        'Surface area (mm²)',
        *zip(*data),
        marker='.',
        line_style='-',
        color='green',
        fig_size=fig_size,
        dpi=dpi)

    fig.savefig(out_file)


def _save_individual(drop: IFTDropAnalysis, drop_dir_name: str, options: IFTAnalysisSaverOptions) -> None:
    full_dir = options.save_root_dir/drop_dir_name
    full_dir.mkdir(parents=True)

    _save_drop_image(drop, out_file_path=full_dir / 'image_original.png')
    _save_drop_image_annotated(drop, out_file_path=full_dir / 'image_annotated.png')

    with (full_dir/'params.ini').open('w') as out_file:
        _save_drop_params(drop, out_file=out_file)

    with (full_dir/'profile_extracted.csv').open('wb') as out_file:
        _save_drop_contour(drop, out_file=out_file)

    with (full_dir/'profile_fit.csv').open('wb') as out_file:
        _save_drop_contour_fit(drop, out_file=out_file)

    with (full_dir/'profile_fit_residuals.csv').open('wb') as out_file:
        _save_drop_contour_fit_residuals(drop, out_file=out_file)

    drop_residuals_figure_opts = options.drop_residuals_figure_opts
    if drop_residuals_figure_opts.bn_should_save.get():
        fig_size = drop_residuals_figure_opts.size
        dpi = drop_residuals_figure_opts.bn_dpi.get()
        with (full_dir/'profile_fit_residuals_plot.png').open('wb') as out_file:
            _save_drop_contour_fit_residuals_figure(
                drop=drop,
                out_file=out_file,
                fig_size=fig_size,
                dpi=dpi)


def save_drops(drops: Iterable[IFTDropAnalysis], options: IFTAnalysisSaverOptions) -> None:
    drops = list(drops)

    full_dir = options.save_root_dir
    assert full_dir.is_dir() or not full_dir.exists()
    full_dir.mkdir(parents=True, exist_ok=True)
    clear_directory_contents(full_dir)

    padding = len(str(len(drops)))
    dir_name = options.bn_save_dir_name.get()
    for i, drop in enumerate(drops):
        drop_dir_name = dir_name + '{i:0>{padding}}'.format(i=i, padding=padding)
        _save_individual(drop, drop_dir_name, options)

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
