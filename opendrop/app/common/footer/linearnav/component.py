from typing import Optional, Callable, Any

from gi.repository import Gtk

from opendrop.mvp import ComponentSymbol, View, Presenter

linear_navigator_footer_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@linear_navigator_footer_cs.view(options=['back_label', 'next_label'])
class LinearNavigatorFooterView(View['LinearNavigatorFooterPresenter', Gtk.Widget]):
    def _do_init(self, back_label: str = '< Back', next_label: str = 'Next >') -> Gtk.Widget:
        self._widget = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            margin=10,
            hexpand=True,
        )

        self._back_btn = Gtk.Button(back_label)
        self._widget.pack_start(self._back_btn, expand=False, fill=False, padding=0)

        self._next_btn = Gtk.Button(next_label)
        self._widget.pack_end(self._next_btn, expand=False, fill=False, padding=0)

        self._back_btn.connect('clicked', lambda *_: self.presenter.back())
        self._next_btn.connect('clicked', lambda *_: self.presenter.next())

        self.presenter.view_ready()

        return self._widget

    def show_back_btn(self) -> None:
        self._back_btn.show()

    def hide_back_btn(self) -> None:
        self._back_btn.hide()

    def show_next_btn(self) -> None:
        self._next_btn.show()

    def hide_next_btn(self) -> None:
        self._next_btn.hide()

    def _do_destroy(self) -> None:
        self._widget.destroy()


@linear_navigator_footer_cs.presenter(options=['do_back', 'do_next'])
class LinearNavigatorFooterPresenter(Presenter['LinearNavigatorFooterView']):
    def _do_init(
            self,
            do_back: Optional[Callable[[], Any]] = None,
            do_next: Optional[Callable[[], Any]] = None
    ) -> None:
        self._do_back = do_back
        self._do_next = do_next

    def view_ready(self) -> None:
        if self._do_back is not None:
            self.view.show_back_btn()
        else:
            self.view.hide_back_btn()

        if self._do_next is not None:
            self.view.show_next_btn()
        else:
            self.view.hide_next_btn()

    def back(self) -> None:
        self._do_back()

    def next(self) -> None:
        self._do_next()
