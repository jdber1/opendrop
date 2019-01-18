import configparser
import itertools
import math
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Sequence, Tuple, Union

import cv2
import numpy as np
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator

from opendrop.app.ift.model.analyser import IFTDropAnalysis
from opendrop.app.validation import validate, check_is_positive, \
    check_is_not_empty
from opendrop.utility.bindable import BuiltinSetBindable, SetBindable
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable


class IFTAnalysisSaverOptions:
    class FigureOptions:
        def __init__(self, should_save: bool, dpi: int, size_w: float, size_h: float) -> None:
            self.bn_should_save = AtomicBindableVar(should_save)
            self.bn_dpi = AtomicBindableVar(dpi)
            self.bn_size_w = AtomicBindableVar(size_w)
            self.bn_size_h = AtomicBindableVar(size_h)

            self.dpi_err = validate(
                value=self.bn_dpi,
                checks=(check_is_not_empty, check_is_positive),
                enabled=self.bn_should_save)(BuiltinSetBindable())
            self.size_w_err = validate(
                value=self.bn_size_w,
                checks=(check_is_not_empty, check_is_positive),
                enabled=self.bn_should_save)(BuiltinSetBindable())
            self.size_h_err = validate(
                value=self.bn_size_h,
                checks=(check_is_not_empty, check_is_positive),
                enabled=self.bn_should_save)(BuiltinSetBindable())

            self.errors = SetBindable.union(self.dpi_err, self.size_w_err, self.size_h_err)

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
            size_w=16,
            size_h=12)
        self.volume_figure_opts = self.FigureOptions(
            should_save=True,
            dpi=300,
            size_w=16,
            size_h=12)
        self.surface_area_figure_opts = self.FigureOptions(
            should_save=True,
            dpi=300,
            size_w=16,
            size_h=12)

        # Validation:

        self.save_dir_parent_err = validate(
            value=self.bn_save_dir_parent,
            checks=(check_is_not_empty,))(BuiltinSetBindable())
        self.save_dir_name_err = validate(
            value=self.bn_save_dir_name,
            checks=(check_is_not_empty,))(BuiltinSetBindable())

        errors = [self.save_dir_parent_err, self.save_dir_name_err]

        for figure_opts in (self.drop_residuals_figure_opts, self.ift_figure_opts, self.volume_figure_opts,
                            self.surface_area_figure_opts):
            errors.append(figure_opts.errors)

        self.errors = SetBindable.union(*errors)

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

def save_drop_image(drop: IFTDropAnalysis, out_file_path: Path) -> None:
    image = drop.image
    if image is None:
        return

    cv2.imwrite(str(out_file_path), image)


def save_drop_image_annotated(drop: IFTDropAnalysis, out_file_path: Path) -> None:
    image, image_annotations = drop.image, drop.image_annotations
    if image is None or image_annotations is None:
        return

    # Note, colors are in BGR format.

    # Draw extracted needle edges
    image = cv2.polylines(
        img=image,
        pts=image_annotations.needle_contours_px,
        isClosed=False,
        color=(255, 128, 0),
        thickness=1,
        lineType=cv2.LINE_AA)

    # Draw extracted drop profile
    image = cv2.polylines(
        img=image,
        pts=[image_annotations.drop_contour_px],
        isClosed=False,
        color=(255, 128, 0),
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
                color=(128, 0, 255),
                thickness=1,
                lineType=cv2.LINE_AA)

    # Draw needle region
    image = cv2.rectangle(
        img=image,
        pt1=image_annotations.needle_region_px.p0,
        pt2=image_annotations.needle_region_px.p1,
        color=(255, 26, 13),
        thickness=1)

    # Draw drop region
    image = cv2.rectangle(
        img=image,
        pt1=image_annotations.drop_region_px.p0,
        pt2=image_annotations.drop_region_px.p1,
        color=(13, 26, 255),
        thickness=1)

    cv2.imwrite(out_file_path, image)


def save_drop_params(drop: IFTDropAnalysis, out_file) -> None:
    if drop.image_annotations is None:
        return

    root = configparser.ConfigParser(allow_no_value=True)
    root.read_dict(OrderedDict((
        ('Physical', OrderedDict((
            ('; all quantities are in SI units', None),
            ('timestamp', drop.image_timestamp),
            ('interfacial_tension', drop.interfacial_tension),
            ('volume', drop.volume),
            ('surface area', drop.surface_area),
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
            ('; angle is in degrees (positive is clockwise)', None),
            ('image_angle', math.degrees(drop.apex_rot)),
        ))),
    )))

    root.write(out_file)


def save_drop_contour(drop: IFTDropAnalysis, out_file) -> None:
    image_annotations = drop.image_annotations
    if image_annotations is None:
        return

    drop_contour = image_annotations.drop_contour_px
    np.savetxt(out_file, drop_contour, fmt='%d,%d')


def save_drop_contour_fit(drop: IFTDropAnalysis, out_file, samples: int = 100) -> None:
    drop_contour_fit = drop.generate_drop_contour_fit(samples=samples)
    if drop_contour_fit is None:
        return

    # Translate (0, 0) to the drop apex coordinates of the image.
    drop_contour_fit += drop.apex_coords_px
    np.savetxt(out_file, drop_contour_fit, fmt='%d,%d')


def save_drop_residuals(drop: IFTDropAnalysis, out_file) -> None:
    residuals = drop.drop_contour_fit_residuals
    if residuals is None:
        return

    np.savetxt(out_file, residuals, fmt='%g,%g')


def save_drop_residuals_figure(drop: IFTDropAnalysis, out_file, fig_size: Tuple[float, float], dpi: int) -> None:
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


def save_ift_figure(drops: Sequence[IFTDropAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
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


def save_volume_figure(drops: Sequence[IFTDropAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
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


def save_surface_area_figure(drops: Sequence[IFTDropAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
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

# save profile_extracted.csv
# save profile_fit.csv # save so it overlays onto image coordinates
# save residuals.csv


def save_drop(drop: IFTDropAnalysis, drop_dir_name: str, options: IFTAnalysisSaverOptions):
    save_drop_dir = options.save_root_dir/drop_dir_name

    # clear the directory

    save_drop_image(drop.image, save_drop_dir)
    save_drop_image_annotated(drop.image, drop.image_annotations, save_drop_dir)
