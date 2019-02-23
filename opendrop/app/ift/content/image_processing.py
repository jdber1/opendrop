from enum import Enum

from gi.repository import Gtk, Gdk

from opendrop.app.common.content.image_processing.expensive_analysis_preview import MaskAnalysis, PolylineAnalysis
from opendrop.app.common.content.image_processing.image_processing import ImageProcessingFormPresenter, \
    ImageProcessingFormView, RectangleView, MaskHighlightView, PolylineView
from opendrop.app.common.content.image_processing.stage.tools import RegionDragToDefine
from opendrop.app.ift.model.image_annotator.image_annotator import IFTImageAnnotator
from opendrop.utility.bindable import BuiltinSetBindable
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindableVar
from opendrop.utility.bindablegext.bindable import GObjectPropertyBindable
from opendrop.utility.geometry import Vector2
from opendrop.utility.validation import add_style_class_when_flags, ErrorsPresenter
from opendrop.widgets.canny_parameters import CannyParameters
from opendrop.widgets.render.objects import PixbufFill, Rectangle, Polyline
from opendrop.widgets.render.objects.rectangle import RectangleWithLabel


class IFTImageProcessingFormPresenter(ImageProcessingFormPresenter['IFTImageProcessingFormView']):
    def __init__(self, image_annotator: IFTImageAnnotator, **kwargs) -> None:
        super().__init__(**kwargs)

        self._image_annotator = image_annotator

        self.__destroyed = False
        self.__cleanup_tasks = []

        # Drop region and needle region defining tools
        self._bn_define_region_mode = AtomicBindableVar(DefineRegionMode.DROP)
        self._drop_region_tool = RegionDragToDefine(canvas_size=Vector2(*self._preview.image.shape[1::-1]))
        self._needle_region_tool = RegionDragToDefine(canvas_size=Vector2(*self._preview.image.shape[1::-1]))

        # Edge detection overlay
        edge_detection_live_analysis = MaskAnalysis(
            mask_out=self._view.edge_detection_overlay.bn_mask,
            preview=self._preview,
            do_analysis=self._image_annotator.apply_edge_detection)
        self.__cleanup_tasks.append(edge_detection_live_analysis.destroy)

        # Drop contour overlay
        drop_contour_live_analysis = PolylineAnalysis(
            polyline_out=self._view.drop_contour_overlay.bn_polyline,
            preview=self._preview,
            do_analysis=self._image_annotator.extract_drop_contour)
        self.__cleanup_tasks.append(drop_contour_live_analysis.destroy)

        data_bindings = [
            self._bn_define_region_mode.bind_to(self._view.bn_define_region_mode),
            self._image_annotator.bn_canny_min.bind_to(self._view.bn_canny_min),
            self._image_annotator.bn_canny_max.bind_to(self._view.bn_canny_max),
            self._image_annotator.bn_drop_region_px.bind_to(self._drop_region_tool.bn_selection),
            self._image_annotator.bn_needle_region_px.bind_to(self._needle_region_tool.bn_selection),

            self._drop_region_tool.bn_selection.bind_to(self._view.drop_region.bn_extents),
            self._needle_region_tool.bn_selection.bind_to(self._view.needle_region.bn_extents),

            self._drop_region_tool.bn_selection_transient.bind_to(self._view.drop_region_transient.bn_extents),
            self._needle_region_tool.bn_selection_transient.bind_to(self._view.needle_region_transient.bn_extents)]
        self.__cleanup_tasks.extend(db.unbind for db in data_bindings)

        event_connections = [
            self._bn_define_region_mode.on_changed.connect(self._update_stage_active_tool),

            self._drop_region_tool.bn_selection.on_changed.connect(self._auto_choose_next_tool),
            self._needle_region_tool.bn_selection.on_changed.connect(self._auto_choose_next_tool),

            self._image_annotator.bn_canny_min.on_changed.connect(edge_detection_live_analysis.reanalyse),
            self._image_annotator.bn_canny_max.on_changed.connect(edge_detection_live_analysis.reanalyse),

            self._image_annotator.bn_canny_min.on_changed.connect(drop_contour_live_analysis.reanalyse),
            self._image_annotator.bn_canny_max.on_changed.connect(drop_contour_live_analysis.reanalyse),
            self._image_annotator.bn_drop_region_px.on_changed.connect(drop_contour_live_analysis.reanalyse),
        ]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

        self._errors = [
            ErrorsPresenter(self._image_annotator.drop_region_px_err, self._view.bn_drop_region_err),
            ErrorsPresenter(self._image_annotator.needle_region_px_err, self._view.bn_needle_region_err)]
        self.__cleanup_tasks.extend(e.destroy for e in self._errors)

        self._auto_choose_next_tool()
        self._update_stage_active_tool()

    def _update_stage_active_tool(self) -> None:
        mode = self._bn_define_region_mode.get()

        if mode is DefineRegionMode.DROP:
            self._stage.active_tool = self._drop_region_tool
        elif mode is DefineRegionMode.NEEDLE:
            self._stage.active_tool = self._needle_region_tool
        else:
            self._stage.active_tool = None

    def _auto_choose_next_tool(self) -> None:
        if self._drop_region_tool.bn_selection.get() is None:
            self._bn_define_region_mode.set(DefineRegionMode.DROP)
        elif self._needle_region_tool.bn_selection.get() is None:
            self._bn_define_region_mode.set(DefineRegionMode.NEEDLE)

    def validate(self) -> bool:
        if not super().validate():
            return False

        for e in self._errors:
            e.show_errors()

        return not self._image_annotator.has_errors

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True

        super().destroy()


class DefineRegionMode(Enum):
    NONE = 0
    DROP = 1
    NEEDLE = 2


class IFTImageProcessingFormView(ImageProcessingFormView):
    STYLE = '''
    .error-text {
        color: red;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        define_region_mode_lbl = Gtk.Label('Cursor is defining:')
        self._toolbar_area.attach(define_region_mode_lbl, 0, 0, 1, 1)

        self._drop_region_mode_inp = Gtk.RadioButton(label='Drop region')
        # self._drop_region_mode_inp.get_style_context().add_class('small-pad')
        self._toolbar_area.attach(self._drop_region_mode_inp, 1, 0, 1, 1)

        self._toolbar_area.attach(Gtk.Label('or'), 2, 0, 1, 1)

        self._needle_region_mode_inp = Gtk.RadioButton.new_with_label_from_widget(self._drop_region_mode_inp,
                                                                                  label='Needle region')
        # self._needle_region_mode_inp.get_style_context().add_class('small-pad')
        self._toolbar_area.attach(self._needle_region_mode_inp, 3, 0, 1, 1)

        canny_edge_detection_lbl = Gtk.Label(xalign=0)
        canny_edge_detection_lbl.set_markup('<b>Canny edge detection:</b>')
        self._extras_area.attach(canny_edge_detection_lbl, 0, 0, 1, 1)

        canny_parameters = CannyParameters()
        self._extras_area.attach(canny_parameters, 0, 1, 1, 1)

        self.widget.show_all()

        # Subviews

        # Edge detection overlay view
        edge_det_overlay = PixbufFill()
        self._stage_render.add_render_object(edge_det_overlay)
        self.edge_detection_overlay = MaskHighlightView(edge_det_overlay)

        # Extracted drop contour view
        drop_contour_overlay = Polyline(stroke_color=(0.0, 0.5, 1.0), stroke_width=2)
        self._stage_render.add_render_object(drop_contour_overlay)
        self.drop_contour_overlay = PolylineView(drop_contour_overlay)

        # Drop and needle region rectangle views
        drop_region_rect_ro = RectangleWithLabel(label='Drop region', border_color=(1.0, 0.1, 0.05))
        self._stage_render.add_render_object(drop_region_rect_ro)
        self.drop_region = RectangleView(drop_region_rect_ro)

        needle_region_rect_ro = RectangleWithLabel(label='Needle region', border_color=(0.05, 0.1, 1.0))
        self._stage_render.add_render_object(needle_region_rect_ro)
        self.needle_region = RectangleView(needle_region_rect_ro)

        drop_region_transient_rect_ro = Rectangle(border_color=(1.0, 0.3, 0.15))
        self._stage_render.add_render_object(drop_region_transient_rect_ro)
        self.drop_region_transient = RectangleView(drop_region_transient_rect_ro)

        needle_region_transient_rect_ro = Rectangle(border_color=(0.15, 0.3, 1.0))
        self._stage_render.add_render_object(needle_region_transient_rect_ro)
        self.needle_region_transient = RectangleView(needle_region_transient_rect_ro)

        self.bn_canny_min = GObjectPropertyBindable(canny_parameters, 'min-thresh')
        self.bn_canny_max = GObjectPropertyBindable(canny_parameters, 'max-thresh')

        # Bindable properties
        self.bn_define_region_mode = AtomicBindableAdapter(setter=self._set_define_region_mode)

        # Error highlighting
        self.bn_drop_region_err = BuiltinSetBindable()
        self.bn_needle_region_err = BuiltinSetBindable()

        self.bn_drop_region_err.__refs = [
            add_style_class_when_flags(self._drop_region_mode_inp, 'error-text', self.bn_drop_region_err)]
        self.bn_needle_region_err.__refs = [
            add_style_class_when_flags(self._needle_region_mode_inp, 'error-text', self.bn_needle_region_err)]

        # Event wiring
        self._drop_region_mode_inp.connect(
            'toggled', lambda w: self.bn_define_region_mode.set(DefineRegionMode.DROP) if w.props.active else None)

        self._needle_region_mode_inp.connect(
            'toggled', lambda w: self.bn_define_region_mode.set(DefineRegionMode.NEEDLE) if w.props.active else None)

    def _set_define_region_mode(self, mode: 'DefineRegionMode') -> None:
        if mode is DefineRegionMode.DROP:
            self._drop_region_mode_inp.props.active = True
        elif mode is DefineRegionMode.NEEDLE:
            self._needle_region_mode_inp.props.active = True
        else:
            raise ValueError
