import functools
from typing import Any, Mapping, Type, Optional

from gi.repository import Gtk
from opendrop.gtk_specific.GtkWidgetView import GtkWidgetView

from opendrop.gtk_specific.GtkWindowView import GtkWindowView
from opendrop.sample_mvp_app.observer_viewer.observer_chooser_dialog.iview import \
    ICameraChooserDialogView


class CameraChooserDialogView(GtkWindowView, ICameraChooserDialogView):
    def setup(self):
        # Outer
        outer = Gtk.VBox(spacing=5)

        self.window.add(outer)

        # Type selection area
        type_selection_outer = Gtk.Box()
        type_selection_outer.set_name('type_selection_outer')

        type_selection_outer_css = Gtk.CssProvider()  # type: Gtk.CssProvider
        type_selection_outer_css.load_from_data(bytes('''
            #type_selection_outer {
                background-color: gainsboro;
            }
        ''', encoding='utf-8'))

        type_selection_outer.get_style_context()\
                            .add_provider(type_selection_outer_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        outer.pack_start(type_selection_outer, expand=False, fill=False, padding=0)

        type_selection = Gtk.Grid(column_spacing=5, row_spacing=5)
        type_selection.props.margin = 5

        type_selection_outer.pack_start(type_selection, expand=True, fill=True, padding=0)

        # Type selection combobox
        type_label = Gtk.Label('Observer Type:', xalign=0)
        type_combo = Gtk.ComboBoxText()
        type_combo.props.hexpand = True

        type_combo.connect('changed', self.handle_type_combo_changed)

        type_selection.attach(type_label, 0, 0, 1, 1)
        type_selection.attach(type_combo, 1, 0, 1, 1)

        self.type_combo = type_combo  # type: Gtk.ComboBoxText

        # Configuration area
        config_area = Gtk.Box()
        config_area.props.margin = 5

        outer.pack_start(config_area, expand=True, fill=True, padding=0)

        self.config_area = config_area  # type: Gtk.Box

        self.config_view = None  # type: Optional[Type[GtkWidgetView]]

        # Submit area
        submit_container_outer = Gtk.Box()
        submit_container_outer.set_name('submit_container_outer')

        submit_container_outer_css = Gtk.CssProvider()  # type: Gtk.CssProvider
        submit_container_outer_css.load_from_data(bytes('''
            #submit_container_outer {
                background-color: gainsboro;
            }
        ''', encoding='utf-8'))

        submit_container_outer.get_style_context()\
                              .add_provider(submit_container_outer_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        outer.pack_start(submit_container_outer, expand=False, fill=False, padding=0)

        submit_container = Gtk.Grid(column_homogeneous=True)

        submit_container_outer.pack_end(submit_container, expand=True, fill=True, padding=0)

        submit_container.get_style_context().add_class('linked')

        # Ok button
        ok_btn = Gtk.Button(label='Ok')
        ok_btn.props.hexpand = True

        ok_btn.connect('clicked', self.events.on_user_submit_button_clicked.fire_ignore_args)

        submit_container.attach(ok_btn, 1, 0, 1, 1)

        # Cancel button
        cancel_btn = Gtk.Button(label='Cancel')
        cancel_btn.props.hexpand = True

        cancel_btn.connect('clicked', self.events.on_user_cancel_button_clicked.fire_ignore_args)

        submit_container.attach(cancel_btn, 0, 0, 1, 1)

        outer.show_all()

    def set_config(self, config_view: GtkWidgetView) -> None:
        self.config_area.pack_start(config_view.container, expand=True, fill=True, padding=0)

    def add_observer_type(self, id: Any, name: str) -> None:
        self.type_combo.append(id, name)

    def handle_type_combo_changed(self, combo: Gtk.ComboBox) -> None:
        self.events.on_type_combo_changed.fire(combo.get_active_id())

    def submit(self, observer_type: Any, camera_opts: Mapping[str, Any]) -> None:
        self.events.on_submit.fire(observer_type, camera_opts)
