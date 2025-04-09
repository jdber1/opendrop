from enum import IntEnum
from typing import Optional

from gi.repository import Gtk, Pango

from opendrop.appfw import Presenter, TemplateChild, component, install


Column = IntEnum(
    'Column',
    """
    ID
    VENDOR
    MODEL
    NAME
    TL_TYPE
    VERSION
    """,
    start=0
)


@component(
    template_path='./chooser.ui',
)
class ImageAcquisitionConfiguratorGenicamCameraChooserPresenter(Presenter):
    tree_view = TemplateChild('tree_view')  # TemplateChild[Gtk.TreeView]
    tree_selection = TemplateChild('tree_selection')  # TemplateChild[Gtk.TreeSelection]
    list_store = TemplateChild('list_store')  # TemplateChild[Gtk.ListStore]

    def after_view_init(self) -> None:
        id_column = Gtk.TreeViewColumn(
            title='ID',
            cell_renderer=Gtk.CellRendererText(ellipsize=Pango.EllipsizeMode.END),
            text=Column.ID,
        )
        id_column.set_expand(True)
        self.tree_view.append_column(id_column)

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Vendor',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.VENDOR,
        ))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Model',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.MODEL,
        ))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Name',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.NAME,
        ))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Interface',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.TL_TYPE,
        ))

        self.tree_view.append_column(Gtk.TreeViewColumn(
            title='Version',
            cell_renderer=Gtk.CellRendererText(),
            text=Column.VERSION,
        ))

    @install
    def get_camera_id(self) -> Optional[str]:
        _, tree_iter = self.tree_selection.get_selected()
        if tree_iter is None: return None

        return self.list_store.get_value(tree_iter, Column.ID)

    @install
    def select_camera_id(self, camera_id: str) -> None:
        if not isinstance(camera_id, str):
            raise TypeError("camera_id must be str, not {}".format(type(camera_id)))

        for row in self.list_store:
            if row[Column.ID] == camera_id:
                break
        else:
            raise ValueError("Camera ID '{}' is not an option".format(camera_id))

        self.tree_selection.select_path(row.path)

    @install
    def append(self, camera_id: str, vendor: str, model: str, name: str, tl_type: str, version: str) -> None:
        row = [''] * len(Column)

        row[Column.ID] = camera_id
        row[Column.VENDOR] = vendor
        row[Column.MODEL] = model
        row[Column.NAME] = name
        row[Column.TL_TYPE] = tl_type
        row[Column.VERSION] = version

        self.list_store.append(row)
