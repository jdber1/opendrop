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

from gi.repository import Gtk, GObject

from opendrop.widgets.float_entry import FloatEntry


class CannyParameters(Gtk.Grid):
    _STYLE = '''
        .small-pad {
             min-height: 0px;
             min-width: 0px;
             padding: 6px 4px 6px 4px;
        }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(_STYLE, 'utf-8'))

    def __init__(self) -> None:
        super().__init__(row_spacing=10, column_spacing=10)

        self._max_thresh_inp = Gtk.Adjustment(value=255, lower=1, upper=255)
        self._min_thresh_inp = Gtk.Adjustment(value=0, lower=0, upper=255)
        self._min_thresh_rel_inp = Gtk.Adjustment(value=0, lower=0, upper=1)

        max_thresh_lbl = Gtk.Label('Max threshold:', halign=Gtk.Align.START)
        self.attach(max_thresh_lbl, 0, 0, 1, 1)

        max_thresh_ety = FloatEntry(width_chars=5, halign=Gtk.Align.END, xalign=0)
        max_thresh_ety.get_style_context().add_class('small-pad')
        max_thresh_ety.get_style_context().add_provider(CannyParameters._STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        self.attach(max_thresh_ety, 2, 0, 1, 1)

        max_thresh_scl = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self._max_thresh_inp,
                                   hexpand=True, draw_value=False)
        max_thresh_scl.get_style_context().add_class('small-pad')
        max_thresh_scl.get_style_context().add_provider(CannyParameters._STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        self.attach(max_thresh_scl, 1, 0, 1, 1)

        min_thresh_lbl = Gtk.Label('Min threshold:', halign=Gtk.Align.START)
        self.attach(min_thresh_lbl, 0, 1, 1, 1)

        min_thresh_ety = FloatEntry(width_chars=5, halign=Gtk.Align.END, xalign=0)
        min_thresh_ety.get_style_context().add_class('small-pad')
        min_thresh_ety.get_style_context().add_provider(CannyParameters._STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        self.attach(min_thresh_ety, 2, 1, 1, 1)

        min_thresh_scl = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self._min_thresh_rel_inp,
                                   hexpand=True, draw_value=False)
        min_thresh_scl.get_style_context().add_class('small-pad')
        min_thresh_scl.get_style_context().add_provider(CannyParameters._STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        self.attach(min_thresh_scl, 1, 1, 1, 1)

        self.show_all()

        # Bind the properties of Gtk.Adjustment to the Gtk.Entry widgets for max/min threshold.
        for (src, targ), prop in itertools.product(
                ((self._max_thresh_inp, max_thresh_ety), (self._min_thresh_inp, min_thresh_ety)),
                ('value', 'lower', 'upper')):
            src.bind_property(
                prop,                               # source_property
                targ, prop,                         # target, target_property
                GObject.BindingFlags.BIDIRECTIONAL  # flags
                | GObject.BindingFlags.SYNC_CREATE,
                lambda _, v: round(v, 1),           # transform_to
                lambda _, v: v                      # transform_from
            )

        self._max_thresh_inp.bind_property(
            'value',
            self._min_thresh_inp, 'upper')

        self._min_thresh_inp.bind_property(
            'value',
            self._min_thresh_rel_inp, 'value',
            GObject.BindingFlags.BIDIRECTIONAL
            | GObject.BindingFlags.SYNC_CREATE,
            lambda _, v: v / self._min_thresh_inp.props.upper,
            lambda _, v: v * self._min_thresh_inp.props.upper)

        self._notify_min_thresh_rel_inp_when_max_thresh_inp_value_changed_hdl_id = \
            self._max_thresh_inp.connect(
                'notify::value',
                # Emit a notify signal on `min_thresh_rel_inp` so that `min_thresh_inp`'s value will be updated to
                # the correct absolute value (by the binding above) since `max_thresh_inp`'s value has changed.
                lambda *_: self._min_thresh_rel_inp.notify('value'))

        self._notify_max_thresh_when_max_thresh_inp_value_changed_hdl_id = \
            self._max_thresh_inp.connect(
                'value-changed',
                lambda *_: self.notify('max-thresh'))

        self._notify_min_thresh_when_min_thresh_inp_value_changed_hdl_id = \
            self._min_thresh_inp.connect(
                'value-changed',
                lambda *_: self.notify('min-thresh'))

    @GObject.Property
    def max_thresh(self) -> float:
        return self._max_thresh_inp.props.value

    @max_thresh.setter
    def max_thresh(self, value: float) -> None:
        self._max_thresh_inp.handler_block(self._notify_min_thresh_rel_inp_when_max_thresh_inp_value_changed_hdl_id)
        self._max_thresh_inp.handler_block(self._notify_max_thresh_when_max_thresh_inp_value_changed_hdl_id)

        self._max_thresh_inp.props.value = value
        self._min_thresh_rel_inp.props.value = self._min_thresh_inp.props.value / value

        self._max_thresh_inp.handler_unblock(self._notify_min_thresh_rel_inp_when_max_thresh_inp_value_changed_hdl_id)
        self._max_thresh_inp.handler_unblock(self._notify_max_thresh_when_max_thresh_inp_value_changed_hdl_id)

    @GObject.Property
    def min_thresh(self) -> float:
        return self._min_thresh_inp.props.value

    @min_thresh.setter
    def min_thresh(self, value: float) -> None:
        self._min_thresh_inp.props.value = value
