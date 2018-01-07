from typing import Any, Type

from opendrop.gtk_specific.GtkWidgetView import GtkWidgetView


class ObserverConfigView(GtkWidgetView):
    OBSERVER_TYPE = None  # type: Any

    @classmethod
    def get_view_for(cls, observer_type: Any) -> Type['ObserverConfigView']:
        for subcls in cls.__subclasses__():
            if subcls.OBSERVER_TYPE == observer_type:
                return subcls
