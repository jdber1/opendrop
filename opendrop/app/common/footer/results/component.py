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
import math
from typing import Callable, Any

from gi.repository import Gtk

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable import VariableBindable
from opendrop.utility.bindable.typing import Bindable
from .model import ResultsFooterStatus
from .progress import progress_cs

results_footer_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@results_footer_cs.view()
class ResultsFooterView(View['ResultsFooterPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.Grid(margin=10, column_spacing=10, vexpand=False)

        self._cancel_or_back_stack = Gtk.Stack(visible=True)
        self._widget.attach(self._cancel_or_back_stack, 0, 0, 1, 1)

        self._cancel_btn = Gtk.Button(hexpand=False, vexpand=True, visible=True)
        self._cancel_or_back_stack.add(self._cancel_btn)

        cancel_btn_inner = Gtk.Grid(visible=True)
        self._cancel_btn.add(cancel_btn_inner)

        cancel_btn_image = Gtk.Image.new_from_icon_name('process-stop', Gtk.IconSize.BUTTON)
        cancel_btn_lbl = Gtk.Label(
            label='Cancel',
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            hexpand=True,
            vexpand=True,
        )

        cancel_btn_image.show()
        cancel_btn_lbl.show()
        cancel_btn_inner.add(cancel_btn_image)
        cancel_btn_inner.add(cancel_btn_lbl)

        self._back_btn = Gtk.Button('< Back', hexpand=False, vexpand=True, visible=True)
        self._cancel_or_back_stack.add(self._back_btn)

        _, progress_area = self.new_component(
            progress_cs.factory(
                in_progress=self.presenter.bn_progress,
                in_progress_label=self.presenter.bn_progress_label,
                in_time_elapsed=self.presenter.bn_time_elapsed,
                in_time_remaining=self.presenter.bn_time_remaining,
            )
        )
        progress_area.show()
        self._widget.attach(progress_area, 1, 0, 1, 1)

        self._save_btn = Gtk.Button(hexpand=False, vexpand=True, visible=True)
        self._widget.attach(self._save_btn, 2, 0, 1, 1)

        save_btn_inner = Gtk.Grid(visible=True)
        self._save_btn.add(save_btn_inner)

        save_btn_image = Gtk.Image.new_from_icon_name('document-save', Gtk.IconSize.BUTTON)
        save_btn_lbl = Gtk.Label(
            label='Save',
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            hexpand=True,
            vexpand=True,
        )

        save_btn_image.show()
        save_btn_lbl.show()
        save_btn_inner.add(save_btn_image)
        save_btn_inner.add(save_btn_lbl)

        self._back_btn.connect('clicked', lambda *_: self.presenter.back())
        self._cancel_btn.connect('clicked', lambda *_: self.presenter.cancel())
        self._save_btn.connect('clicked', lambda *_: self.presenter.save())

        self.presenter.view_ready()

        return self._widget

    def show_back_btn(self) -> None:
        self._cancel_or_back_stack.props.visible_child = self._back_btn

    def show_cancel_btn(self) -> None:
        self._cancel_or_back_stack.props.visible_child = self._cancel_btn

    def enable_save_btn(self) -> None:
        self._save_btn.props.sensitive = True

    def disable_save_btn(self) -> None:
        self._save_btn.props.sensitive = False

    def _do_destroy(self) -> None:
        self._widget.destroy()


@results_footer_cs.presenter(
    options=[
        'in_status',
        'in_progress',
        'in_time_elapsed',
        'in_time_remaining',
        'do_back',
        'do_cancel',
        'do_save',
    ]
)
class ResultsFooterPresenter(Presenter['ResultsFooterView']):
    def _do_init(
            self,
            in_status: Bindable[ResultsFooterStatus],
            in_progress: Bindable[float],
            in_time_elapsed: Bindable[float],
            in_time_remaining: Bindable[float],
            do_back: Callable[[], Any],
            do_cancel: Callable[[], Any],
            do_save: Callable[[], Any],
    ) -> None:
        self._bn_status = in_status
        self._bn_time_remaining = in_time_remaining
        self._do_back = do_back
        self._do_cancel = do_cancel
        self._do_save = do_save

        self.bn_progress = in_progress
        self.bn_progress_label = VariableBindable('')
        self.bn_time_elapsed = in_time_elapsed
        self.bn_time_remaining = VariableBindable(math.nan)

        self.__event_connections = []

    def view_ready(self) -> None:
        self.__event_connections.extend([
            self._bn_status.on_changed.connect(
                self._hdl_status_changed
            ),
            self._bn_time_remaining.on_changed.connect(
                self._hdl_time_remaining_changed
            ),
        ])

        self._hdl_status_changed()
        self._hdl_time_remaining_changed()

    def _hdl_status_changed(self) -> None:
        status = self._bn_status.get()

        if status is ResultsFooterStatus.IN_PROGRESS:
            self.bn_progress_label.set('')
            self.view.show_cancel_btn()
            self.view.disable_save_btn()
        elif status is ResultsFooterStatus.FINISHED:
            self.bn_progress_label.set('Finished')
            self.view.show_back_btn()
            self.view.enable_save_btn()
        elif status is ResultsFooterStatus.CANCELLED:
            self.bn_progress_label.set('Cancelled')
            self.view.show_back_btn()
            self.view.enable_save_btn()

    def _hdl_time_remaining_changed(self) -> None:
        time_remaining = self._bn_time_remaining.get()
        self.bn_time_remaining.set(time_remaining)

    def back(self) -> None:
        self._do_back()

    def cancel(self) -> None:
        self._do_cancel()

    def save(self) -> None:
        self._do_save()

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
