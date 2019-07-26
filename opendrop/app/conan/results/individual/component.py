from gi.repository import Gtk

from opendrop.mvp import ComponentSymbol, View, Presenter
from .detail import detail_cs
from .master import master_cs
from .model import IndividualModel

individual_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@individual_cs.view()
class IndividualView(View['IndividualPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, position=400)

        _, detail_area = self.new_component(
            detail_cs.factory(
                in_analysis=self.presenter.bn_selection,
            )
        )
        detail_area.show()
        self._widget.pack1(detail_area, resize=True, shrink=False)

        _, master_area = self.new_component(
            master_cs.factory(
                in_analyses=self.presenter.bn_analyses,
                bind_selection=self.presenter.bn_selection,
            )
        )
        master_area.show()
        self._widget.pack2(master_area, resize=True, shrink=False)

        return self._widget

    def _do_destroy(self) -> None:
        self._widget.destroy()


@individual_cs.presenter(options=['model'])
class IndividualPresenter(Presenter['IndividualView']):
    def _do_init(self, model: IndividualModel) -> None:
        self._model = model
        self.bn_analyses = model.bn_analyses
        self.bn_selection = model.bn_selection
