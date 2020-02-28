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
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
from gi.repository import Gtk, Gdk, GObject

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable.gextension import GObjectPropertyBindable
from opendrop.widgets.float_entry import FloatEntry
from opendrop.widgets.integer_entry import IntegerEntry
from .model import FigureOptions

figure_options_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@figure_options_cs.view(options=['figure_name'])
class FigureOptionsView(View['FigureOptionsPresenter', Gtk.Widget]):
    STYLE = '''
    .small-pad {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
    }

    .error {
        color: red;
        border: 1px solid red;
    }

    .error-text {
        color: red;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def _do_init(self, figure_name: str) -> Gtk.Widget:
        self._widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self._should_save_figure_inp = Gtk.CheckButton(label='Save {}'.format(figure_name))
        self._widget.add(self._should_save_figure_inp)

        self._more_options = Gtk.Grid(margin_left=30, row_spacing=5, column_spacing=10)
        self._widget.add(self._more_options)

        dpi_lbl = Gtk.Label('Figure DPI:', xalign=0)
        self._more_options.attach(dpi_lbl, 0, 0, 1, 1)

        dpi_inp_ctn = Gtk.Grid()
        self._more_options.attach_next_to(dpi_inp_ctn, dpi_lbl, Gtk.PositionType.RIGHT, 1, 1)
        dpi_inp = IntegerEntry(value=300, lower=72, upper=10000, width_chars=5)
        dpi_inp.get_style_context().add_class('small-pad')
        dpi_inp_ctn.add(dpi_inp)

        dpi_err_lbl = Gtk.Label(xalign=0, width_request=190)
        dpi_err_lbl.get_style_context().add_class('error-text')
        self._more_options.attach_next_to(dpi_err_lbl, dpi_inp_ctn, Gtk.PositionType.RIGHT, 1, 1)

        size_lbl = Gtk.Label('Figure size (cm):', xalign=0)
        self._more_options.attach(size_lbl, 0, 1, 1, 1)

        size_inp_ctn = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self._more_options.attach_next_to(size_inp_ctn, size_lbl, Gtk.PositionType.RIGHT, 1, 1)

        size_w_lbl = Gtk.Label('W:')
        size_inp_ctn.add(size_w_lbl)
        size_w_inp = FloatEntry(value=10, lower=0, upper=10000, width_chars=6)
        size_w_inp.get_style_context().add_class('small-pad')

        size_inp_ctn.add(size_w_inp)
        size_h_lbl = Gtk.Label('H:')
        size_inp_ctn.add(size_h_lbl)

        size_h_inp = FloatEntry(value=10, lower=0, upper=10000, width_chars=6)
        size_h_inp.get_style_context().add_class('small-pad')
        size_inp_ctn.add(size_h_inp)

        size_err_lbl = Gtk.Label(xalign=0, width_request=190)
        size_err_lbl.get_style_context().add_class('error-text')
        self._more_options.attach_next_to(size_err_lbl, size_inp_ctn, Gtk.PositionType.RIGHT, 1, 1)

        self._should_save_figure_inp.bind_property(
            'active',                          # source_property
            self._more_options,                # target
            'sensitive',                       # target_property
            GObject.BindingFlags.SYNC_CREATE,  # flags
        )

        self.bn_should_save = GObjectPropertyBindable(
            g_obj=self._should_save_figure_inp,
            prop_name='active',
        )

        self.bn_dpi = GObjectPropertyBindable(
            g_obj=dpi_inp,
            prop_name='value',
        )

        self.bn_size_w = GObjectPropertyBindable(
            g_obj=size_w_inp,
            prop_name='value',
        )

        self.bn_size_h = GObjectPropertyBindable(
            g_obj=size_h_inp,
            prop_name='value',
        )

        self.presenter.view_ready()

        self._widget.show_all()

        return self._widget

    def _do_destroy(self) -> None:
        self._widget.destroy()


@figure_options_cs.presenter(options=['model'])
class FigureOptionsPresenter(Presenter['FigureOptionsView']):
    def _do_init(self, model: FigureOptions) -> None:
        self._model = model
        self.__data_bindings = []

    def view_ready(self) -> None:
        self.__data_bindings.extend([
            self._model.bn_should_save.bind(self.view.bn_should_save),
            self._model.bn_dpi.bind(self.view.bn_dpi),
            self._model.bn_size_w.bind(self.view.bn_size_w),
            self._model.bn_size_h.bind(self.view.bn_size_h),
        ])

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()
