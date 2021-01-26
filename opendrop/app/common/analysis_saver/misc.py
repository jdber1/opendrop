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


import itertools
import math
from typing import Optional, Sequence, Tuple, Union

import cv2
import numpy as np
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator

from opendrop.utility.geometry import Line2, Rect2, Vector2

INCHES_PER_CM = 0.393701


def simple_grapher(label_x: str, label_y: str, data_x: Sequence[float], data_y: Sequence[float], color: str,
                   marker: str, line_style: str, fig_size: Tuple[float, float], *,
                   tick_x_interval: Optional[float] = None,
                   xlim: Union[str, Tuple[float, float]] = 'tight',
                   grid: bool = True,
                   dpi: int = 300):
    # TODO: Handle when data_x/data_y is an empty sequence.

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


def draw_line(image: np.ndarray, line: Line2, color: Tuple[float, float, float], thickness: int = 1) -> None:
    image_extents = Rect2(position=(0, 0), size=image.shape[1::-1])

    start_point = line.eval(x=image_extents.x0)
    end_point = line.eval(x=image_extents.x1)

    if not image_extents.contains(start_point):
        if start_point.y < image_extents.y0:
            y_to_eval = image_extents.y0
        else:
            y_to_eval = image_extents.y1
        start_point = line.eval(y=y_to_eval)

    if not image_extents.contains(end_point):
        if end_point.y < image_extents.y0:
            y_to_eval = image_extents.y0
        else:
            y_to_eval = image_extents.y1
        end_point = line.eval(y=y_to_eval)

    cv2.line(image,
             pt1=tuple(start_point.map(int)),
             pt2=tuple(end_point.map(int)),
             color=color,
             thickness=thickness)


def draw_angle_marker(image: np.ndarray, vertex_pos: Vector2[float], start_angle: float, delta_angle: float, radius: float,
                      color: Tuple[float, float, float]) -> None:
    if not Rect2(position=(0, 0), size=image.shape[1::-1]).contains(vertex_pos):
        # Vertex is outside of the image, ignore.
        return

    end_angle = start_angle + delta_angle

    start_pos = vertex_pos
    delta_pos = radius * Vector2(math.cos(-end_angle), math.sin(-end_angle))
    end_pos = start_pos + delta_pos

    cv2.line(image,
             pt1=tuple(start_pos.map(int)),
             pt2=tuple(end_pos.map(int)),
             color=color,
             thickness=1)
