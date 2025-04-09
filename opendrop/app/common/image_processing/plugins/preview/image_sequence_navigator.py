# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
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


import gc

from gi.repository import Gtk

from opendrop.app.common.image_processing.plugins.preview.model import ImageSequenceAcquirerController
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable.gextension import GObjectPropertyBindable
from opendrop.widgets.integer_entry import IntegerEntry

image_sequence_navigator_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@image_sequence_navigator_cs.view()
class ImageSequenceNavigatorView(View['ImageSequenceNavigatorPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Grid:
        self._widget = Gtk.Grid(column_spacing=5)

        left_btn = Gtk.Button('<')
        self._widget.attach(left_btn, 0, 0, 1, 1)

        self._idx_inp = IntegerEntry(lower=1, width_chars=3)
        self._widget.attach(self._idx_inp, 1, 0, 1, 1)

        self._num_images_lbl = Gtk.Label()
        self._widget.attach(self._num_images_lbl, 2, 0, 1, 1)

        right_btn = Gtk.Button('>')
        self._widget.attach(right_btn, 3, 0, 1, 1)

        self.bn_show_index = GObjectPropertyBindable(
            g_obj=self._idx_inp,
            prop_name='value',
            # User input is 1-based indexing
            transform_to=lambda x: x+1 if x is not None else None,
            transform_from=lambda x: x-1 if x is not None else None,
        )
        self._idx_inp.connect('activate', lambda *_: self.presenter.view_show_idx_changed())
        self._idx_inp.connect('focus-out-event', lambda *_: self.presenter.view_show_idx_changed())

        left_btn.connect('clicked', lambda *_: self.presenter.prev_image())
        right_btn.connect('clicked', lambda *_: self.presenter.next_image())

        self._widget.show_all()

        self.presenter.view_ready()

        return self._widget

    def set_num_images(self, num_images: int) -> None:
        self._num_images_lbl.props.label = (
            'of {}'
            .format(num_images)
        )

        self._idx_inp.props.upper = num_images

    def hide(self) -> None:
        self._widget.hide()

    def show(self) -> None:
        self._widget.show()

    def _do_destroy(self) -> None:
        self._widget.destroy()


@image_sequence_navigator_cs.presenter(options=['model'])
class ImageSequenceNavigatorPresenter(Presenter['ImageSequenceNavigatorView']):
    def _do_init(self, model: ImageSequenceAcquirerController) -> None:
        self._model = model
        self.__data_bindings = []
        self.__event_connections = []
        gc.collect()

    def view_ready(self) -> None:
        self.__data_bindings.extend([
            self._model.bn_showing_image_index.bind_to(
                self.view.bn_show_index
            ),
        ])

        self.__event_connections.extend([
            self._model.bn_num_images.on_changed.connect(
                self._hdl_model_num_images_changed,
            ),
        ])

        self._hdl_model_num_images_changed()

    def view_show_idx_changed(self) -> None:
        showing_idx = self.view.bn_show_index.get()
        self._model.bn_showing_image_index.set(showing_idx)

    def _hdl_model_num_images_changed(self) -> None:
        num_images = self._model.bn_num_images.get()

        if num_images <= 1:
            self.view.hide()
        else:
            self.view.show()

        self.view.set_num_images(num_images)

    def next_image(self) -> None:
        showing_idx = self._model.bn_showing_image_index.get()
        if showing_idx is None:
            return

        next_idx = showing_idx + 1
        next_idx %= self._model.bn_num_images.get()

        self._model.bn_showing_image_index.set(
            next_idx
        )

    def prev_image(self) -> None:
        showing_idx = self._model.bn_showing_image_index.get()
        if showing_idx is None:
            return

        prev_idx = showing_idx - 1
        prev_idx %= self._model.bn_num_images.get()

        self._model.bn_showing_image_index.set(
            prev_idx
        )

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()

        for ec in self.__event_connections:
            ec.disconnect()
