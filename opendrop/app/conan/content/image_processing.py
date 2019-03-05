from enum import Enum

from gi.repository import Gtk, Gdk

from opendrop.app.common.content.image_processing.expensive_analysis_preview import MaskAnalysis, PolylineAnalysis
from opendrop.app.common.content.image_processing.image_processing import ImageProcessingFormPresenter, \
    ImageProcessingFormView, RectangleView, MaskHighlightView, PolylineView, LineView
from opendrop.app.common.content.image_processing.stage.tools import RegionDragToDefine, LineDragToDefine
from opendrop.app.conan.model.image_annotator.image_annotator import ConanImageAnnotator
from opendrop.utility.events import Event
from opendrop.utility.simplebindable import AccessorBindable, BoxBindable
from opendrop.utility.simplebindablegext import GObjectPropertyBindable
from opendrop.utility.geometry import Vector2
from opendrop.utility.validation import add_style_class_when_flags, ErrorsPresenter
from opendrop.widgets.canny_parameters import CannyParameters
from opendrop.widgets.render.objects import Line, PixbufFill, Polyline, Rectangle, RectangleWithLabel


class ConanImageProcessingFormPresenter(ImageProcessingFormPresenter['ConanImageProcessingFormView']):
    _errors = tuple()

    def __init__(self, image_annotator: ConanImageAnnotator, **kwargs) -> None:
        super().__init__(**kwargs)

        self._image_annotator = image_annotator

        self.__destroyed = False
        self.__cleanup_tasks = []

        if self._preview is None:
            return

        # Drop region and surface line defining tools
        self._bn_define_feature_mode = BoxBindable(DefineFeatureMode.DROP)
        self._drop_region_tool = RegionDragToDefine(canvas_size=Vector2(*self._preview.image.shape[1::-1]))
        self._surface_line_tool = LineDragToDefine(canvas_size=Vector2(*self._preview.image.shape[1::-1]))

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
            do_analysis=self._image_annotator.extract_drop_contours)
        self.__cleanup_tasks.append(drop_contour_live_analysis.destroy)

        data_bindings = [
            self._bn_define_feature_mode.bind_to(self._view.bn_define_feature_mode),

            self._image_annotator.bn_canny_min.bind_to(self._view.bn_canny_min),
            self._image_annotator.bn_canny_max.bind_to(self._view.bn_canny_max),
            self._image_annotator.bn_using_needle.bind_to(self._view.bn_using_needle),
            self._image_annotator.bn_drop_region_px.bind_to(self._drop_region_tool.bn_selection),
            self._image_annotator.bn_surface_line_px.bind_to(self._surface_line_tool.bn_selection),

            self._drop_region_tool.bn_selection.bind_to(self._view.drop_region.bn_extents),
            self._surface_line_tool.bn_selection.bind_to(self._view.surface_line.bn_line),

            self._drop_region_tool.bn_selection_transient.bind_to(self._view.drop_region_transient.bn_extents),
            self._surface_line_tool.bn_selection_transient.bind_to(self._view.surface_line_transient.bn_line)]
        self.__cleanup_tasks.extend(db.unbind for db in data_bindings)

        event_connections = [
            self._view.on_select_new_mode.connect(self._change_tool),

            self._drop_region_tool.bn_selection.on_changed.connect(self._auto_choose_next_tool),
            self._surface_line_tool.bn_selection.on_changed.connect(self._auto_choose_next_tool),

            self._image_annotator.bn_canny_min.on_changed.connect(edge_detection_live_analysis.reanalyse),
            self._image_annotator.bn_canny_max.on_changed.connect(edge_detection_live_analysis.reanalyse),

            self._image_annotator.bn_canny_min.on_changed.connect(drop_contour_live_analysis.reanalyse),
            self._image_annotator.bn_canny_max.on_changed.connect(drop_contour_live_analysis.reanalyse),
            self._image_annotator.bn_drop_region_px.on_changed.connect(drop_contour_live_analysis.reanalyse),
            self._image_annotator.bn_using_needle.on_changed.connect(drop_contour_live_analysis.reanalyse),
            self._image_annotator.bn_surface_line_px.on_changed.connect(drop_contour_live_analysis.reanalyse),
        ]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

        self._errors = [
            ErrorsPresenter(self._image_annotator.drop_region_px_err, self._view.bn_drop_region_err),
            ErrorsPresenter(self._image_annotator.surface_line_px_err, self._view.bn_surface_line_err)]
        self.__cleanup_tasks.extend(e.destroy for e in self._errors)

        self._auto_choose_next_tool()
        self._change_tool(self._bn_define_feature_mode.get())

    def _change_tool(self, mode: 'DefineFeatureMode') -> None:
        if mode is DefineFeatureMode.DROP:
            self._stage.active_tool = self._drop_region_tool
        elif mode is DefineFeatureMode.SURFACE:
            self._stage.active_tool = self._surface_line_tool
        else:
            self._stage.active_tool = None

        self._bn_define_feature_mode.set(mode)

    def _auto_choose_next_tool(self) -> None:
        if self._drop_region_tool.bn_selection.get() is None:
            self._bn_define_feature_mode.set(DefineFeatureMode.DROP)
        elif self._surface_line_tool.bn_selection.get() is None:
            self._bn_define_feature_mode.set(DefineFeatureMode.SURFACE)

    def validate(self) -> bool:
        for e in self._errors:
            e.show_errors()

        return not self._image_annotator.has_errors

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True

        super().destroy()


class DefineFeatureMode(Enum):
    DROP = 1
    SURFACE = 2


class ConanImageProcessingFormView(ImageProcessingFormView):
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

        self.on_select_new_mode = Event()

        define_region_mode_lbl = Gtk.Label('Cursor is defining:')
        self._toolbar_area.attach(define_region_mode_lbl, 0, 0, 1, 1)

        self._drop_region_mode_inp = Gtk.RadioButton(label='Drop region', focus_on_click=False)
        self._toolbar_area.add(self._drop_region_mode_inp)

        self._toolbar_area.add(Gtk.Label('or'))

        self._surface_line_mode_inp = Gtk.RadioButton.new_with_label_from_widget(self._drop_region_mode_inp,
                                                                                 label='Surface line')
        self._surface_line_mode_inp.props.focus_on_click = False

        self._toolbar_area.add(self._surface_line_mode_inp)

        using_needle_inp_lbl = Gtk.Label(xalign=0)
        using_needle_inp_lbl.set_markup('<b>Drop profile extraction:</b>')
        using_needle_inp = Gtk.CheckButton(label='Using needle')

        # Not really needed.
        # self._extras_area.attach(using_needle_inp_lbl, 0, 0, 1, 1)
        # self._extras_area.attach(using_needle_inp, 0, 1, 1, 1)

        canny_edge_detection_lbl = Gtk.Label(xalign=0)
        canny_edge_detection_lbl.set_markup('<b>Canny edge detection:</b>')
        self._extras_area.attach(canny_edge_detection_lbl, 0, 2, 1, 1)

        canny_parameters = CannyParameters()
        self._extras_area.attach(canny_parameters, 0, 3, 1, 1)

        self.widget.show_all()

        # Subviews

        # Edge detection overlay view
        edge_det_overlay = PixbufFill()
        self._stage_render.add_render_object(edge_det_overlay)
        self.edge_detection_overlay = MaskHighlightView(edge_det_overlay, color=(0, 0, 255, 100))

        # Extracted drop contour view
        drop_contour_overlay_ro = Polyline(stroke_color=(0.0, 0.5, 1.0))
        self._stage_render.add_render_object(drop_contour_overlay_ro)
        self.drop_contour_overlay = PolylineView(drop_contour_overlay_ro)

        # Drop region and surface line views
        drop_region_ro = RectangleWithLabel(label='Drop region', border_color=(1.0, 0.1, 0.05))
        self._stage_render.add_render_object(drop_region_ro)
        self.drop_region = RectangleView(drop_region_ro)

        surface_line_ro = Line(stroke_color=(0.1, 0.8, 0.1))
        self._stage_render.add_render_object(surface_line_ro)
        self.surface_line = LineView(surface_line_ro)

        drop_region_transient_ro = Rectangle(border_color=(1.0, 0.3, 0.15))
        self._stage_render.add_render_object(drop_region_transient_ro)
        self.drop_region_transient = RectangleView(drop_region_transient_ro)

        surface_line_transient_ro = Line(stroke_color=(0.2, 1.0, 0.2), draw_control_points=True)
        self._stage_render.add_render_object(surface_line_transient_ro)
        self.surface_line_transient = LineView(surface_line_transient_ro)

        # Bindable properties
        self.bn_define_feature_mode = AccessorBindable(setter=self._set_define_feature_mode)

        self.bn_canny_min = GObjectPropertyBindable(canny_parameters, 'min-thresh')
        self.bn_canny_max = GObjectPropertyBindable(canny_parameters, 'max-thresh')

        self.bn_using_needle = GObjectPropertyBindable(using_needle_inp, 'active')

        # Error highlighting
        self.bn_drop_region_err = BoxBindable(set())
        self.bn_surface_line_err = BoxBindable(set())

        self.bn_drop_region_err.__refs = [
            add_style_class_when_flags(self._drop_region_mode_inp, 'error-text', self.bn_drop_region_err)]
        self.bn_surface_line_err.__refs = [
            add_style_class_when_flags(self._surface_line_mode_inp, 'error-text', self.bn_surface_line_err)]

        # Event wiring
        self._drop_region_mode_inp.connect(
            'toggled', lambda w: self.on_select_new_mode.fire(DefineFeatureMode.DROP) if w.props.active else None)

        self._surface_line_mode_inp.connect(
            'toggled', lambda w: self.on_select_new_mode.fire(DefineFeatureMode.SURFACE) if w.props.active else None)

    def _set_define_feature_mode(self, mode: 'DefineFeatureMode') -> None:
        if mode is DefineFeatureMode.DROP:
            self._drop_region_mode_inp.props.active = True
        elif mode is DefineFeatureMode.SURFACE:
            self._surface_line_mode_inp.props.active = True
        else:
            raise ValueError
