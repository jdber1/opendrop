import csv
import math
from pathlib import Path
from typing import Optional, Sequence, Tuple, Iterable

import cv2
import numpy as np

from opendrop.app.common.model.analysis_saver import FigureOptions, simple_grapher, draw_line, draw_angle_marker
from opendrop.app.conan.model.analyser import ConanDropAnalysis
from opendrop.utility.bindable import SetBindable
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable
from opendrop.utility.misc import clear_directory_contents
from opendrop.utility.validation import validate, check_is_not_empty


# Save options container

class ConanAnalysisSaverOptions:
    def __init__(self) -> None:
        self.bn_save_dir_parent = AtomicBindableVar(None)  # type: AtomicBindable[Optional[Path]]
        self.bn_save_dir_name = AtomicBindableVar('')  # type: AtomicBindable[str]

        self.angle_figure_opts = FigureOptions(
            should_save=True,
            dpi=300,
            size_w=10,
            size_h=10)

        # Validation:

        self.save_dir_parent_err = validate(
            value=self.bn_save_dir_parent,
            checks=(check_is_not_empty,))
        self.save_dir_name_err = validate(
            value=self.bn_save_dir_name,
            checks=(check_is_not_empty,))

        errors = [self.save_dir_parent_err, self.save_dir_name_err, self.angle_figure_opts.errors]
        self._errors = SetBindable.union(*errors)

    @property
    def has_errors(self) -> bool:
        return bool(self._errors)

    @property
    def save_root_dir(self) -> Path:
        return self.bn_save_dir_parent.get() / self.bn_save_dir_name.get()


def save_drops(drops: Iterable[ConanDropAnalysis], options: ConanAnalysisSaverOptions) -> None:
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

    figure_opts = options.angle_figure_opts
    if figure_opts.bn_should_save.get():
        fig_size = figure_opts.size
        dpi = figure_opts.bn_dpi.get()
        with (full_dir/'left_angle_plot.png').open('wb') as out_file:
            _save_left_angle_figure(
                drops=drops,
                out_file=out_file,
                fig_size=fig_size,
                dpi=dpi)
        with (full_dir/'right_angle_plot.png').open('wb') as out_file:
            _save_right_angle_figure(
                drops=drops,
                out_file=out_file,
                fig_size=fig_size,
                dpi=dpi)


def _save_individual(drop: ConanDropAnalysis, drop_dir_name: str, options: ConanAnalysisSaverOptions) -> None:
    full_dir = options.save_root_dir/drop_dir_name
    full_dir.mkdir(parents=True)

    _save_drop_image(drop, out_file_path=full_dir / 'image_original.png')
    _save_drop_image_annotated(drop, out_file_path=full_dir / 'image_annotated.png')

    with (full_dir/'profile_extracted.csv').open('wb') as out_file:
        _save_drop_contour(drop, out_file=out_file)

    with (full_dir/'tangents.csv').open('wb') as out_file:
        _save_drop_contact_tangents(drop, out_file=out_file)

    with (full_dir/'surface.csv').open('wb') as out_file:
        _save_surface_line(drop, out_file=out_file)


def _save_drop_image(drop: ConanDropAnalysis, out_file_path: Path) -> None:
    image = drop.image
    if image is None:
        return

    cv2.imwrite(str(out_file_path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def _save_drop_image_annotated(drop: ConanDropAnalysis, out_file_path: Path) -> None:
    image, image_annotations = drop.image, drop.image_annotations
    if image is None or image_annotations is None:
        return

    # Draw on a copy
    image = image.copy()

    # Draw extracted drop profile
    image = cv2.polylines(
        img=image,
        pts=image_annotations.drop_contours_px,
        isClosed=False,
        color=(0, 128, 255),
        thickness=1,
        lineType=cv2.LINE_AA)

    # Draw drop region
    image = cv2.rectangle(
        img=image,
        pt1=tuple(image_annotations.drop_region_px.p0),
        pt2=tuple(image_annotations.drop_region_px.p1),
        color=(255, 26, 13),
        thickness=1)

    # Draw surface line
    draw_line(image, image_annotations.surface_line_px, color=(64, 255, 64))

    # Draw angle markers
    surface_angle = -math.atan(image_annotations.surface_line_px.gradient)

    # Draw left angle marker
    draw_angle_marker(
        image=image,
        vertex_pos=drop.bn_left_point.get(),
        start_angle=math.pi + surface_angle,
        delta_angle=-drop.bn_left_angle.get(),
        radius=int(0.1 * image.shape[0]),
        color=(255, 0, 128))

    # Draw right angle marker
    draw_angle_marker(
        image=image,
        vertex_pos=drop.bn_right_point.get(),
        start_angle=surface_angle,
        delta_angle=drop.bn_right_angle.get(),
        radius=int(0.1 * image.shape[0]),
        color=(255, 0, 128))

    cv2.imwrite(str(out_file_path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def _save_drop_contour(drop: ConanDropAnalysis, out_file) -> None:
    image_annotations = drop.image_annotations
    if image_annotations is None:
        return

    drop_contours = image_annotations.drop_contours_px
    if len(drop_contours) == 0:
        return

    drop_contour = np.vstack(image_annotations.drop_contours_px)
    np.savetxt(out_file, drop_contour, fmt='%d,%d')


def _save_drop_contact_tangents(drop: ConanDropAnalysis, out_file) -> None:
    left_tangent = drop.bn_left_tangent.get()
    right_tangent = drop.bn_right_tangent.get()

    tangents = np.vstack((left_tangent, right_tangent))
    np.savetxt(out_file, tangents, fmt='%.18e,%.18e')


def _save_surface_line(drop: ConanDropAnalysis, out_file) -> None:
    image_annotations = drop.image_annotations
    if image_annotations is None:
        return

    surface_line = image_annotations.surface_line_px
    coefficients = np.array([surface_line.gradient, surface_line.eval_at(x=0).y])
    coefficients = coefficients.reshape(1, 2)
    np.savetxt(out_file, coefficients, fmt='%.18e,%.18e')


def _save_left_angle_figure(drops: Sequence[ConanDropAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [drop for drop in drops if math.isfinite(drop.image_timestamp) and
                                       math.isfinite(drop.bn_left_angle.get())]
    start_time = min(drop.image_timestamp for drop in drops)
    data = ((drop.image_timestamp - start_time, math.degrees(drop.bn_left_angle.get())) for drop in drops)

    fig = simple_grapher(
        'Time (s)',
        'Left angle (degrees)',
        *zip(*data),
        marker='.',
        line_style='-',
        color='blue',
        fig_size=fig_size,
        dpi=dpi)

    fig.savefig(out_file)


def _save_right_angle_figure(drops: Sequence[ConanDropAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [drop for drop in drops if math.isfinite(drop.image_timestamp) and
                                       math.isfinite(drop.bn_right_angle.get())]
    start_time = min(drop.image_timestamp for drop in drops)
    data = ((drop.image_timestamp - start_time, math.degrees(drop.bn_right_angle.get())) for drop in drops)

    fig = simple_grapher(
        'Time (s)',
        'Right angle (degrees)',
        *zip(*data),
        marker='.',
        line_style='-',
        color='blue',
        fig_size=fig_size,
        dpi=dpi)

    fig.savefig(out_file)


def _save_timeline_data(drops: Sequence[ConanDropAnalysis], out_file) -> None:
    writer = csv.writer(out_file)
    writer.writerow([
        'Time (s)',
        'Left angle (degrees)',
        'Right angle (degrees)',
        'Left contact x-coordinate (px)',
        'Left contact y-coordinate (px)',
        'Right contact x-coordinate (px)',
        'Right contact y-coordinate (px)',
    ])

    for drop in drops:
        writer.writerow([
            drop.image_timestamp,
            math.degrees(drop.bn_left_angle.get()),
            math.degrees(drop.bn_right_angle.get()),
            *drop.bn_left_point.get(),
            *drop.bn_right_point.get(),
        ])
