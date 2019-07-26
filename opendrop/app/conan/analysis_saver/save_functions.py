import csv
import math
from pathlib import Path
from typing import Sequence, Tuple, Iterable

import cv2
import numpy as np

from opendrop.app.common.analysis_saver.misc import simple_grapher, draw_line, draw_angle_marker
from opendrop.app.conan.analysis import ConanAnalysis
from opendrop.utility.misc import clear_directory_contents
from .model import ConanAnalysisSaverOptions


def save_drops(drops: Iterable[ConanAnalysis], options: ConanAnalysisSaverOptions) -> None:
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


def _save_individual(drop: ConanAnalysis, drop_dir_name: str, options: ConanAnalysisSaverOptions) -> None:
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


def _save_drop_image(drop: ConanAnalysis, out_file_path: Path) -> None:
    if drop.is_image_replicated:
        # A copy of the image already exists somewhere, we don't need to save it again.
        return

    image = drop.bn_image.get()
    if image is None:
        return

    cv2.imwrite(str(out_file_path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def _save_drop_image_annotated(drop: ConanAnalysis, out_file_path: Path) -> None:
    image = drop.bn_image.get()
    if image is None:
        return

    # Draw on a copy
    image = image.copy()

    drop_profile_extract = drop.bn_drop_profile_extract.get()
    if drop_profile_extract is not None:
        # Draw extracted drop profile
        image = cv2.polylines(
            img=image,
            pts=[drop_profile_extract],
            isClosed=False,
            color=(0, 128, 255),
            thickness=1,
            lineType=cv2.LINE_AA
        )

    # Draw drop region
    drop_region = drop.bn_drop_region.get()
    if drop_region is not None:
        drop_region = drop_region.as_type(int)
        image = cv2.rectangle(
            img=image,
            pt1=tuple(drop_region.p0),
            pt2=tuple(drop_region.p1),
            color=(255, 26, 13),
            thickness=1
        )

    # Draw surface line
    surface_line = drop.bn_surface_line.get()
    if surface_line is not None:
        draw_line(image, surface_line, color=(64, 255, 64))

    # Draw angle markers
    surface_angle = -math.atan(surface_line.gradient) if surface_line is not None else math.nan

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


def _save_drop_contour(drop: ConanAnalysis, out_file) -> None:
    drop_profile_extract = drop.bn_drop_profile_extract.get()
    if drop_profile_extract is None or len(drop_profile_extract) == 0:
        return

    np.savetxt(out_file, drop_profile_extract, fmt='%.1f,%.1f')


def _save_drop_contact_tangents(drop: ConanAnalysis, out_file) -> None:
    left_tangent = drop.bn_left_tangent.get()
    right_tangent = drop.bn_right_tangent.get()

    tangents = np.vstack((left_tangent, right_tangent))
    np.savetxt(out_file, tangents, fmt='%.6e,%.6e')


def _save_surface_line(drop: ConanAnalysis, out_file) -> None:
    surface_line = drop.bn_surface_line.get()
    if surface_line is None:
        return

    coefficients = np.array([surface_line.gradient, surface_line.eval_at(x=0).y])
    coefficients = coefficients.reshape(1, 2)
    np.savetxt(out_file, coefficients, fmt='%.6e,%.6e')


def _save_left_angle_figure(drops: Sequence[ConanAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [
        drop
        for drop in drops
        if math.isfinite(drop.bn_image_timestamp.get()) and
           math.isfinite(drop.bn_left_angle.get())
    ]

    data = [*zip(*(
        (drop.bn_image_timestamp.get(), math.degrees(drop.bn_left_angle.get()))
        for drop in drops
    ))]

    fig = simple_grapher(
        'Time (s)',
        'Left angle (degrees)',
        *data,
        marker='.',
        line_style='-',
        color='blue',
        fig_size=fig_size,
        dpi=dpi
    )

    fig.savefig(out_file)


def _save_right_angle_figure(drops: Sequence[ConanAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [
        drop
        for drop in drops
        if math.isfinite(drop.bn_image_timestamp.get()) and
           math.isfinite(drop.bn_right_angle.get())
    ]

    data = [*zip(*(
        (drop.bn_image_timestamp.get(), math.degrees(drop.bn_right_angle.get()))
        for drop in drops
    ))]

    fig = simple_grapher(
        'Time (s)',
        'Right angle (degrees)',
        *data,
        marker='.',
        line_style='-',
        color='blue',
        fig_size=fig_size,
        dpi=dpi
    )

    fig.savefig(out_file)


def _save_timeline_data(drops: Sequence[ConanAnalysis], out_file) -> None:
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
        timestamp = drop.bn_image_timestamp.get()
        left_angle = math.degrees(drop.bn_left_angle.get())
        left_point = drop.bn_left_point.get()
        right_angle = math.degrees(drop.bn_right_angle.get())
        right_point = drop.bn_right_point.get()

        writer.writerow([
            format(timestamp, '.1f'),
            format(left_angle, '.1f'),
            format(right_angle, '.1f'),
            format(left_point.x, '.1f'),
            format(left_point.y, '.1f'),
            format(right_point.x, '.1f'),
            format(right_point.y, '.1f'),
        ])
