import collections
from abc import abstractmethod
from enum import Enum
from operator import attrgetter
from typing import TypeVar, Callable, Optional, Generic, Mapping, Type, Any, Sequence

from gi.repository import Gtk

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackView, StackModel, StackPresenter
from opendrop.mytypes import Destroyable
from opendrop.utility.bindable import AtomicBindableVar
from .sidebar import TasksSidebarView, TasksSidebarPresenter

PresenterType = TypeVar('PresenterType', bound=Destroyable)


class WizardPageID(Enum):
    def __init__(self, title: str) -> None:
        self.title = title


WizardViewType = TypeVar('WizardViewType')
PageIDType = TypeVar('PageIDType', bound=WizardPageID)
AnotherPageIDType = TypeVar('AnotherPageIDType', bound=WizardPageID)


class WizardPresenter(Generic[WizardViewType, PageIDType]):
    class PageEntry(Generic[AnotherPageIDType]):
        def __init__(self,
                     page_id: AnotherPageIDType,
                     presenter: Type['WizardPagePresenter'],
                     dependency_factory: Callable[[], Mapping[str, Any]]) -> None:
            self.page_id = page_id
            self.presenter = presenter
            self.dependency_factory = dependency_factory

    def __init__(self, page_entries: Sequence[PageEntry[PageIDType]], view: WizardViewType) -> None:
        self._page_entries = page_entries
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

        self._current_page = None  # type: Optional[WizardPagePresenter]
        self._page_idx = None  # type: Optional[int]

        # UI stuff
        self._page_options = collections.OrderedDict(
            (page_id, AtomicBindableVar(False))
            for page_id in self._page_order)

        self._sidebar_presenter = TasksSidebarPresenter(
            task_and_is_active=tuple(self._page_options.items()),
            view=self._view.sidebar_view)
        self.__cleanup_tasks.append(self._sidebar_presenter.destroy)

        self.__cleanup_tasks.append(lambda: self._go_to_page(None))

    def _activate_first_page(self) -> None:
        self._page_idx = 0
        self._go_to_page(self._page_idx)

    def _prev_page(self) -> None:
        prev_page_idx = self._page_idx - 1
        if prev_page_idx < 0:
            return

        self._page_idx = prev_page_idx
        self._go_to_page(self._page_idx)

    def _next_page(self) -> None:
        next_page_idx = self._page_idx + 1
        if next_page_idx >= len(self._page_order):
            return

        self._page_idx = next_page_idx
        self._go_to_page(self._page_idx)

    def _go_to_page(self, page_idx: Optional[int]) -> None:
        self._unbind_current_page_view()

        if page_idx is None:
            return

        page_id = self._page_order[page_idx]
        page_view = self._view.activate_page(page_id)
        page = self._bind_page_view(page_id, page_view)

        self._current_page  = page

        self._page_options[page_id].set(True)

    def _unbind_current_page_view(self) -> None:
        if self._current_page is None:
            return

        self._current_page.destroy()
        self._current_page = None

    def _bind_page_view(self, page_id: PageIDType, page_view: 'WizardPageView') -> 'WizardPagePresenter':
        page_entry = self._get_page_entry_from_id(page_id)
        page = page_entry.presenter(page_view)
        deps = page_entry.dependency_factory()
        page._page_init(**deps)

        return page

    def _get_page_entry_from_id(self, page_id: PageIDType) -> PageEntry:
        for entry in self._page_entries:
            if entry.page_id is page_id:
                return entry
        else:
            raise ValueError('No page entry found for id `{}`'.format(page_id))

    @property
    def _page_order(self) -> Sequence[PageIDType]:
        return tuple(entry.page_id for entry in self._page_entries)

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True


class WizardPagePresenter:
    def __init__(self, view: 'WizardPageView') -> None:
        self._view = view

    @abstractmethod
    def _page_init(self, **kwargs) -> None:
        pass

    def destroy(self) -> None:
        pass


class WizardView(Generic[PageIDType], GtkWidgetView[Gtk.Grid]):
    def __init__(self) -> None:
        self.widget = Gtk.Grid()

        # Sidebar
        self.sidebar_view = TasksSidebarView(attrgetter('title'))  # type: TasksSidebarView[PageIDType]
        self.widget.attach(self.sidebar_view.widget, 0, 0, 1, 1)

        # Main content container
        self._content_model = StackModel()
        self._content_view = StackView()
        self._content_presenter = StackPresenter(self._content_model, self._content_view)
        self.widget.attach(self._content_view.widget, 1, 0, 1, 1)

        # Main content and Footer separator
        self.widget.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, 1, 2, 1)

        # Footer container
        self._footer_model = StackModel()
        self._footer_view = StackView()
        self._footer_presenter = StackPresenter(self._footer_model, self._footer_view)
        self.widget.attach(self._footer_view.widget, 0, 2, 2, 1)

        self.widget.show_all()

    def _add_page(self, page_id: 'PageIDType', content: GtkWidgetView, footer: GtkWidgetView) -> None:
        self._content_model.add_child(page_id, content)
        self._footer_model.add_child(page_id, footer)

    def activate_page(self, page_id: 'PageIDType') -> 'WizardPageView':
        self._content_model.visible_child_key = page_id
        self._footer_model.visible_child_key = page_id

        return WizardPageView(
            form=self._content_model.get_child_from_key(page_id),
            footer=self._footer_model.get_child_from_key(page_id))


class WizardPageView:
    def __init__(self, form: GtkWidgetView, footer: GtkWidgetView) -> None:
        self.form = form
        self.footer = footer
