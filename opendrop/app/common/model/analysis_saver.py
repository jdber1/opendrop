import itertools
import math
from typing import Optional, Sequence, Tuple, Union

import cv2
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator

from opendrop.mytypes import Image
from opendrop.utility.geometry import Line2, Rect2, Vector2
from opendrop.utility.simplebindable import apply as bn_apply, BoxBindable
from opendrop.utility.validation import check_is_positive
from opendrop.utility.validation import validate, check_is_not_empty


class FigureOptions:
    def __init__(self, should_save: bool, dpi: int, size_w: float, size_h: float) -> None:
        self.bn_should_save = BoxBindable(should_save)
        self.bn_dpi = BoxBindable(dpi)
        self.bn_size_w = BoxBindable(size_w)
        self.bn_size_h = BoxBindable(size_h)

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

        self.errors = bn_apply(set.union, self.dpi_err, self.size_w_err, self.size_h_err)

    @property
    def size(self) -> Tuple[float, float]:
        return self.bn_size_w.get(), self.bn_size_h.get()


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


def draw_line(image: Image, line: Line2, color: Tuple[float, float, float], thickness: int = 1) -> None:
    image_extents = Rect2(pos=(0, 0), size=image.shape[1::-1])

    start_point = line.eval_at(x=image_extents.x0)
    end_point = line.eval_at(x=image_extents.x1)

    if not image_extents.contains_point(start_point):
        if start_point.y < image_extents.y0:
            y_to_eval = image_extents.y0
        else:
            y_to_eval = image_extents.y1
        start_point = line.eval_at(y=y_to_eval)

    if not image_extents.contains_point(end_point):
        if end_point.y < image_extents.y0:
            y_to_eval = image_extents.y0
        else:
            y_to_eval = image_extents.y1
        end_point = line.eval_at(y=y_to_eval)

    cv2.line(image,
             pt1=tuple(start_point.as_type(int)),
             pt2=tuple(end_point.as_type(int)),
             color=color,
             thickness=thickness)


def draw_angle_marker(image: Image, vertex_pos: Vector2[float], start_angle: float, delta_angle: float, radius: float,
                      color: Tuple[float, float, float]) -> None:
    if not Rect2(pos=(0, 0), size=image.shape[1::-1]).contains_point(vertex_pos):
        # Vertex is outside of the image, ignore.
        return

    end_angle = start_angle + delta_angle

    start_pos = vertex_pos
    delta_pos = radius * Vector2(math.cos(-end_angle), math.sin(-end_angle))
    end_pos = start_pos + delta_pos

    cv2.line(image,
             pt1=tuple(start_pos.as_type(int)),
             pt2=tuple(end_pos.as_type(int)),
             color=color,
             thickness=1)
