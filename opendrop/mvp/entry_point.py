from opendrop.mvp.component import ComponentSymbol, Component


class EntryPoint:
    root_component = None  # type: ComponentSymbol

    def start(self, **options) -> None:
        assert self.root_component is not None
        self._component = self.root_component.factory(**options).create()
        self._component.on_destroyed.connect(self._on_component_destroyed)

    def _on_component_destroyed(self, component: Component) -> None:
        self._do_stop()

    def _do_stop(self) -> None:
        pass
