import asyncio
from enum import Enum
from typing import Optional, Callable, Tuple

import cv2
import numpy as np
from gi.repository import Gtk, Gdk, GObject

from opendrop.app.common.model.image_acquisition.image_acquisition import ImageAcquisitionPreview
from opendrop.app.ift.model.image_annotator.image_annotator import IFTImageAnnotator
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.image_acquisition_preview_config import ImageAcquisitionPreviewConfigView, \
    ImageAcquisitionPreviewConfigPresenter
from opendrop.component.message_text_view import MessageTextView
from opendrop.component.mouse_switch import MouseSwitchTarget, MouseSwitch
from opendrop.component.stack import StackModel, StackView, StackPresenter
from opendrop.mytypes import Image
from opendrop.utility.bindable.bindable import AtomicBindable, AtomicBindableAdapter, AtomicBindableVar
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.utility.events import Event
from opendrop.utility.geometry import Rect2, Vector2
from opendrop.utility.gtk_misc import pixbuf_from_array
from opendrop.utility.misc import clamp
from opendrop.widgets.canny_parameters import CannyParameters
from opendrop.widgets.layered_drawing_area.layered_drawing_area import LayeredDrawingArea
from opendrop.widgets.layered_drawing_area.pixbuf_layer import PixbufLayer
from opendrop.widgets.layered_drawing_area.rectangle_layer import RectangleLayer, RectangleWithLabelLayer

MaybeTransformationVector2 = Callable[[Vector2], Optional[Vector2]]


class IFTImageProcessingFormView(StackView):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bn_visible = AtomicBindableAdapter()  # type: AtomicBindableAdapter[bool]
        link_atomic_bn_adapter_to_g_prop(self.bn_visible, self.widget, 'visible')


class _ActualView(GtkWidgetView[Gtk.Grid]):
    class DefineRegionMode(Enum):
        NONE = 0
        DROP = 1
        NEEDLE = 2

    class CannyParametersWrapperView:
        def __init__(self, canny_parameters: CannyParameters) -> None:
            self.bn_max_thresh = AtomicBindableAdapter()  # type: AtomicBindableAdapter[float]
            self.bn_min_thresh = AtomicBindableAdapter()  # type: AtomicBindableAdapter[float]
            link_atomic_bn_adapter_to_g_prop(self.bn_max_thresh, canny_parameters, 'max-thresh')
            link_atomic_bn_adapter_to_g_prop(self.bn_min_thresh, canny_parameters, 'min-thresh')

    class ImageView:
        def __init__(self, layer: PixbufLayer) -> None:
            self._layer = layer
            self.bn_image = AtomicBindableAdapter(setter=self._set_image)  # type: AtomicBindable[Optional[Image]]

        def _set_image(self, image: Optional[Image]) -> None:
            if image is None:
                self._layer.props.source_pixbuf = None
                return

            self._layer.props.source_pixbuf = pixbuf_from_array(image)

    class EdgeDetectionOverlayView:
        EDGE_HIGHLIGHT_COLOUR = (127, 127, 255, 255)  # RGBA

        def __init__(self, layer: PixbufLayer) -> None:
            self._layer = layer
            self.bn_edge_mask = AtomicBindableAdapter(setter=self._set_edge_mask)  # type: AtomicBindable[Optional[Image]]

        def _set_edge_mask(self, mask: Optional[Image]) -> None:
            if mask is None:
                self._layer.props.source_pixbuf = None
                return

            surface = np.zeros(mask.shape + (4,), dtype='uint8')
            surface[mask.astype(bool)] = self.EDGE_HIGHLIGHT_COLOUR

            self._layer.props.source_pixbuf = pixbuf_from_array(surface)

    class DefineRegionView:
        def __init__(self, layer: RectangleLayer, widget_coord_from_image_coord: MaybeTransformationVector2,
                     image_coord_from_widget_coord: MaybeTransformationVector2, mouse_switch_target: MouseSwitchTarget)\
                -> None:
            self._layer = layer
            self._widget_coord_from_image_coord = widget_coord_from_image_coord
            self._image_coord_from_widget_coord = image_coord_from_widget_coord
            self._mouse_switch_target = mouse_switch_target
            self._mouse_switch_target.cursor_name = 'crosshair'

            self._valid_widget_region = None  # type: Optional[Rect2]

            self._region_cache = None  # type: Optional[Rect2]
            self.bn_region = AtomicBindableAdapter(setter=self._set_region)

            self.on_define_start = Event()
            self.on_define_stop = Event()
            self.on_define_move = Event()

            self._mouse_switch_target.do_mouse_button_press = self._do_mouse_button_press
            self._mouse_switch_target.do_mouse_button_release = self._do_mouse_button_release
            self._mouse_switch_target.do_mouse_move = self._do_mouse_move

        def _do_mouse_button_press(self, coord: Vector2) -> None:
            valid_widget_region = self._valid_widget_region
            if valid_widget_region is not None and not valid_widget_region.contains_point(coord):
                return

            image_coord = self._image_coord_from_widget_coord(coord)
            if image_coord is None:
                return

            self.on_define_start.fire(image_coord)

        def _do_mouse_button_release(self, coord: Vector2) -> None:
            valid_widget_region = self._valid_widget_region
            if valid_widget_region is not None and not valid_widget_region.contains_point(coord):
                coord = (clamp(coord[0], valid_widget_region.x0, valid_widget_region.x1),
                         clamp(coord[1], valid_widget_region.y0, valid_widget_region.y1))

            image_coord = self._image_coord_from_widget_coord(coord)
            if image_coord is None:
                return

            self.on_define_stop.fire(image_coord)

        def _do_mouse_move(self, coord: Vector2) -> None:
            valid_widget_region = self._valid_widget_region
            if valid_widget_region is not None and not valid_widget_region.contains_point(coord):
                self._mouse_switch_target.cursor_name = None
                coord = (clamp(coord[0], valid_widget_region.x0, valid_widget_region.x1),
                         clamp(coord[1], valid_widget_region.y0, valid_widget_region.y1))
            else:
                self._mouse_switch_target.cursor_name = 'crosshair'

            image_coord = self._image_coord_from_widget_coord(coord)
            if image_coord is None:
                return

            self.on_define_move.fire(image_coord)

        def _set_region(self, rect: Rect2) -> None:
            self._region_cache = rect

            if rect is None:
                draw_p0 = None
                draw_p1 = None
            else:
                draw_p0 = self._widget_coord_from_image_coord(rect.p0)
                draw_p1 = self._widget_coord_from_image_coord(rect.p1)

            if draw_p0 is None or draw_p1 is None:
                self._layer.props.extents = None
                return

            self._layer.props.extents = Rect2(p0=draw_p0, p1=draw_p1)

        def _redraw_region(self) -> None:
            self._set_region(self._region_cache)

    class ErrorsView:
        def __init__(self, view: '_ActualView') -> None:
            self._view = view

            self.bn_drop_region_err_msg = AtomicBindableAdapter(
                setter=self._set_drop_region_err_msg)  # type: AtomicBindable[Optional[str]]
            self.bn_needle_region_err_msg = AtomicBindableAdapter(
                setter=self._set_needle_region_err_msg)  # type: AtomicBindable[Optional[str]]

            self.bn_drop_region_touched = AtomicBindableVar(False)
            self.bn_needle_region_touched = AtomicBindableVar(False)

        def reset_touches(self) -> None:
            self.bn_drop_region_touched.set(False)
            self.bn_needle_region_touched.set(False)

        def touch_all(self) -> None:
            self.bn_drop_region_touched.set(True)
            self.bn_needle_region_touched.set(True)

        def _set_drop_region_err_msg(self, err_msg: Optional[str]) -> None:
            if err_msg is not None:
                self._view._drop_region_mode_inp.get_style_context().add_class('error')
            else:
                self._view._drop_region_mode_inp.get_style_context().remove_class('error')

        def _set_needle_region_err_msg(self, err_msg: Optional[str]) -> None:
            if err_msg is not None:
                self._view._needle_region_mode_inp.get_style_context().add_class('error')
            else:
                self._view._needle_region_mode_inp.get_style_context().remove_class('error')

    STYLE = '''
    .small-pad {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def __init__(self) -> None:
        self.widget = Gtk.Grid()

        define_regions_ctn = Gtk.Grid(row_spacing=10)
        self.widget.attach(define_regions_ctn, 0, 0, 1, 1)

        define_regions_lbl = Gtk.Label(margin_left=10, margin_right=10, margin_top=10, xalign=0)
        define_regions_lbl.set_markup('<b>Preview, and define regions:</b>')
        define_regions_ctn.attach(define_regions_lbl, 0, 0, 1, 1)

        define_region_mode_ctn = Gtk.Grid(margin_left=10, margin_right=10, column_spacing=5)
        define_regions_ctn.attach(define_region_mode_ctn, 0, 1, 1, 1)

        define_region_mode_lbl = Gtk.Label('Cursor is defining:')
        define_region_mode_ctn.attach(define_region_mode_lbl, 0, 0, 1, 1)

        self._drop_region_mode_inp = Gtk.ToggleButton('Drop region')
        self._drop_region_mode_inp.get_style_context().add_class('small-pad')
        define_region_mode_ctn.attach(self._drop_region_mode_inp, 1, 0, 1, 1)

        define_region_mode_ctn.attach(Gtk.Label('or'), 2, 0, 1, 1)

        self._needle_region_mode_inp = Gtk.ToggleButton('Needle region')
        self._needle_region_mode_inp.get_style_context().add_class('small-pad')
        define_region_mode_ctn.attach(self._needle_region_mode_inp, 3, 0, 1, 1)

        preview_lda = LayeredDrawingArea(hexpand=True, vexpand=True)
        preview_lda.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.FOCUS_CHANGE_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        define_regions_ctn.attach(preview_lda, 0, 2, 1, 1)

        # Preview image layer
        preview_image_lyr = PixbufLayer()
        preview_lda.add_layer(preview_image_lyr)

        # Edge detection overlay layer
        edge_det_overlay_lyr = PixbufLayer()
        preview_lda.add_layer(edge_det_overlay_lyr)

        # Drop region overlay layer
        drop_region_lyr = RectangleWithLabelLayer(label='Drop region', border_colour=(1.0, 0.1, 0.05))
        preview_lda.add_layer(drop_region_lyr)

        # Needle region overlay layer
        needle_region_lyr = RectangleWithLabelLayer(label='Needle region', border_colour=(0.05, 0.1, 1.0))
        preview_lda.add_layer(needle_region_lyr)

        image_acquisition_preview_config_ctn = Gtk.Grid()
        define_regions_ctn.attach(image_acquisition_preview_config_ctn, 0, 3, 1, 1)

        # Mouse switch
        self._define_region_mouse_switch = MouseSwitch(preview_lda)

        # Drop region mouse switch target
        self._drop_mouse_switch_targ = MouseSwitchTarget()

        # Needle region mouse switch target
        self._needle_mouse_switch_targ = MouseSwitchTarget()

        self.widget.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, 1, 1, 1)

        form_ctn = Gtk.Grid(margin=10, row_spacing=10)
        self.widget.attach(form_ctn, 0, 2, 1, 1)

        canny_edge_detection_lbl = Gtk.Label(xalign=0)
        canny_edge_detection_lbl.set_markup('<b>Canny edge detection:</b>')
        form_ctn.attach(canny_edge_detection_lbl, 0, 0, 1, 1)

        canny_parameters = CannyParameters()
        form_ctn.attach(canny_parameters, 0, 1, 1, 1)

        self.widget.show_all()

        # Subviews

        # Image acquisition preview config view
        self.image_acquisition_preview_config_view = ImageAcquisitionPreviewConfigView()
        image_acquisition_preview_config_ctn.add(self.image_acquisition_preview_config_view.widget)
        self.image_acquisition_preview_config_view.widget.show()

        # Image acquisition preview view
        self.image_acquisition_preview_view = _ActualView.ImageView(preview_image_lyr)

        # Edge detection overlay view
        self.edge_detection_overlay_view = _ActualView.EdgeDetectionOverlayView(edge_det_overlay_lyr)

        # Define drop region view
        self.drop_region_view = _ActualView.DefineRegionView(
            layer=drop_region_lyr,
            widget_coord_from_image_coord=preview_image_lyr.draw_coord_from_source_coord,
            image_coord_from_widget_coord=preview_image_lyr.source_coord_from_draw_coord,
            mouse_switch_target=self._drop_mouse_switch_targ)

        # Define needle region view
        self.needle_region_view = _ActualView.DefineRegionView(
            layer=needle_region_lyr,
            widget_coord_from_image_coord=preview_image_lyr.draw_coord_from_source_coord,
            image_coord_from_widget_coord=preview_image_lyr.source_coord_from_draw_coord,
            mouse_switch_target=self._needle_mouse_switch_targ)

        def _hdl_preview_image_lyr_notify_last_draw_extents(preview_image_lyr: PixbufLayer, pspec: GObject.GParamSpec) \
                -> None:
            self.drop_region_view._redraw_region()
            self.needle_region_view._redraw_region()
            self.drop_region_view._valid_widget_region = preview_image_lyr.props.last_draw_extents
            self.needle_region_view._valid_widget_region = preview_image_lyr.props.last_draw_extents

        preview_image_lyr.connect('notify::last-draw-extents', _hdl_preview_image_lyr_notify_last_draw_extents)

        # Canny parameters view
        self.canny_parameters_view = _ActualView.CannyParametersWrapperView(canny_parameters)

        # Bindable properties
        self._define_region_mode = _ActualView.DefineRegionMode.NONE
        self.bn_define_region_mode = AtomicBindableAdapter(self._get_define_region_mode, self._set_define_region_mode)

        # Event wiring
        self._hdl_drop_region_mode_inp_toggled_notify_id = self._drop_region_mode_inp.connect(
            'toggled', self._hdl_drop_region_mode_inp_toggled)
        
        self._hdl_needle_region_mode_inp_toggled_notify_id = self._needle_region_mode_inp.connect(
            'toggled', self._hdl_needle_region_mode_inp_toggled)

        self.errors_view = self.ErrorsView(self)

    def _hdl_drop_region_mode_inp_toggled(self, widget: Gtk.ToggleButton) -> None:
        if widget.props.active:
            self.bn_define_region_mode.set(_ActualView.DefineRegionMode.DROP)
        else:
            self.bn_define_region_mode.set(_ActualView.DefineRegionMode.NONE)

    def _hdl_needle_region_mode_inp_toggled(self, widget: Gtk.ToggleButton) -> None:
        if widget.props.active:
            self.bn_define_region_mode.set(_ActualView.DefineRegionMode.NEEDLE)
        else:
            self.bn_define_region_mode.set(_ActualView.DefineRegionMode.NONE)

    def _get_define_region_mode(self) -> '_ActualView.DefineRegionMode':
        return self._define_region_mode

    def _set_define_region_mode(self, mode: '_ActualView.DefineRegionMode') -> None:
        self._define_region_mode = mode

        self._drop_region_mode_inp.handler_block(self._hdl_drop_region_mode_inp_toggled_notify_id)
        self._needle_region_mode_inp.handler_block(self._hdl_needle_region_mode_inp_toggled_notify_id)

        if mode is _ActualView.DefineRegionMode.NONE:
            self._drop_region_mode_inp.props.active = False
            self._needle_region_mode_inp.props.active = False
            self._define_region_mouse_switch.target = None
        elif mode is _ActualView.DefineRegionMode.DROP:
            self._drop_region_mode_inp.props.active = True
            self._needle_region_mode_inp.props.active = False
            self._define_region_mouse_switch.target = self._drop_mouse_switch_targ
        elif mode is _ActualView.DefineRegionMode.NEEDLE:
            self._drop_region_mode_inp.props.active = False
            self._needle_region_mode_inp.props.active = True
            self._define_region_mouse_switch.target = self._needle_mouse_switch_targ

        self._drop_region_mode_inp.handler_unblock(self._hdl_drop_region_mode_inp_toggled_notify_id)
        self._needle_region_mode_inp.handler_unblock(self._hdl_needle_region_mode_inp_toggled_notify_id)


class _ActualPresenter:
    class CannyEdgeDetectionPresenter:
        def __init__(self, image_annotator: IFTImageAnnotator,
                     view: _ActualView.CannyParametersWrapperView)\
                -> None:
            self._image_annotator = image_annotator
            self._view = view

            self.__data_bindings = [
                Binding(self._image_annotator.bn_canny_min_thresh, self._view.bn_min_thresh),
                Binding(self._image_annotator.bn_canny_max_thresh, self._view.bn_max_thresh),
            ]

        def destroy(self) -> None:
            for db in self.__data_bindings:
                db.unbind()

    class EdgeDetectionOverlayPresenter:
        def __init__(self, image_annotator: IFTImageAnnotator, preview: ImageAcquisitionPreview,
                     view: _ActualView.EdgeDetectionOverlayView) \
                -> None:
            self._loop = asyncio.get_event_loop()

            self._image_annotator = image_annotator
            self._preview = preview
            self._view = view

            self.__event_connections = [
                self._image_annotator.bn_canny_min_thresh.on_changed.connect(
                    self._update_overlay_progressive),
                self._image_annotator.bn_canny_max_thresh.on_changed.connect(
                    self._update_overlay_progressive),
                self._preview.bn_image.on_changed.connect(self._update_overlay)
            ]

            self._update_overlay_progressive_timer_handle = None  # type: Optional[asyncio.TimerHandle]

            self._update_overlay()

        def _update_overlay(self, downsample: Optional[Tuple[int, int]] = None) -> None:
            image_size = tuple(self._preview.bn_image.get().shape[1::-1])

            if downsample is not None:
                downsample = (min(image_size[0], downsample[0]), min(image_size[1], downsample[1]))
                if downsample == image_size:
                    downsample = None

            overlay = self._preview.bn_image.get()

            if downsample is not None:
                # Downsample for faster computation
                overlay = cv2.resize(overlay, dsize=downsample)

            overlay = self._image_annotator.apply_edge_detection(overlay)

            if downsample is not None:
                image_aspect = image_size[0] / image_size[1]
                down_sample_aspect = downsample[0] / downsample[1]
                overlay = cv2.resize(overlay, dsize=None, fx=image_aspect/down_sample_aspect, fy=1)

            self._view.bn_edge_mask.set(overlay)

        def _update_overlay_progressive(self, downsample: Optional[Tuple[int, int]] = (512, 512)) -> None:
            if self._update_overlay_progressive_timer_handle is not None:
                self._update_overlay_progressive_timer_handle.cancel()
                self._update_overlay_progressive_timer_handle = None

            self._update_overlay(downsample=downsample)

            if downsample is None:
                return

            image_size = tuple(self._preview.bn_image.get().shape[1::-1])

            # Just set the next down sample to be the image size
            next_down_sample = image_size

            if next_down_sample[0] >= image_size[0] or next_down_sample[1] >= image_size[1]:
                next_down_sample = None

            self._update_overlay_progressive_timer_handle = self._loop.call_later(
                0.05, self._update_overlay_progressive, next_down_sample)

        def destroy(self) -> None:
            for ec in self.__event_connections:
                ec.disconnect()

    class DefineRegionPresenter:
        def __init__(self, model_bn_region: AtomicBindable[Optional[Rect2]],
                     view: _ActualView.DefineRegionView) -> None:
            self._model_bn_region = model_bn_region
            self._view = view

            self._draw_start = None  # type: Optional[Tuple[float, float]]
            self._new_region_defined = False

            self.on_new_region_defined = Event()

            self.__event_connections = [
                self._view.on_define_start.connect(self._hdl_view_define_start),
                self._view.on_define_stop.connect(self._hdl_view_define_stop),
                self._view.on_define_move.connect(self._hdl_view_define_move)
            ]

            self.__data_bindings = [
                Binding(self._model_bn_region, self._view.bn_region)
            ]

        def _hdl_view_define_start(self, mouse_pos: Tuple[float, float]) -> None:
            self._draw_start = mouse_pos

        def _hdl_view_define_stop(self, mouse_pos: Tuple[float, float]) -> None:
            if self._new_region_defined:
                self.on_new_region_defined.fire()

            self._draw_start = None
            self._new_region_defined = False

        def _hdl_view_define_move(self, mouse_pos: Tuple[float, float]) -> None:
            if not self._draw_start:
                return

            if mouse_pos == self._draw_start:
                return

            self._model_bn_region.set(Rect2(p0=self._draw_start, p1=mouse_pos))
            self._new_region_defined = True

        def destroy(self) -> None:
            for ec in self.__event_connections:
                ec.disconnect()

            for db in self.__data_bindings:
                db.unbind()

    class ErrorsPresenter:
        def __init__(self, validator: IFTImageAnnotator.Validator, view: _ActualView.ErrorsView) -> None:
            self._validator = validator
            self._view = view

            self.__event_connections = [
                self._validator.bn_drop_region_px_err_msg.on_changed.connect(self._update_errors),
                self._validator.bn_needle_region_px_err_msg.on_changed.connect(self._update_errors),

                self._view.bn_drop_region_touched.on_changed.connect(self._update_errors),
                self._view.bn_needle_region_touched.on_changed.connect(self._update_errors),
            ]

            self._view.reset_touches()
            self._update_errors()

        def _update_errors(self) -> None:
            drop_region_err_msg = None  # type: Optional[str]
            needle_region_err_msg = None  # type: Optional[str]

            if self._view.bn_drop_region_touched.get():
                drop_region_err_msg = self._validator.bn_drop_region_px_err_msg.get()

            if self._view.bn_needle_region_touched.get():
                needle_region_err_msg = self._validator.bn_needle_region_px_err_msg.get()

            self._view.bn_drop_region_err_msg.set(drop_region_err_msg)
            self._view.bn_needle_region_err_msg.set(needle_region_err_msg)

        def _clear_errors(self) -> None:
            self._view.bn_drop_region_err_msg.set(None)
            self._view.bn_needle_region_err_msg.set(None)

        def destroy(self) -> None:
            self._clear_errors()
            for ec in self.__event_connections:
                ec.disconnect()

    def __init__(self, image_annotator: IFTImageAnnotator, preview: ImageAcquisitionPreview,
                 view: _ActualView) -> None:
        self._image_annotator = image_annotator
        self._preview = preview
        self._view = view

        preview_config = self._preview.config

        self._view.image_acquisition_preview_config_view.configure_for_config(preview_config)
        config_view_impl = self._view.image_acquisition_preview_config_view.impl

        self._preview_config_presenter = ImageAcquisitionPreviewConfigPresenter(preview_config, config_view_impl)
        self._drop_region_presenter = _ActualPresenter.DefineRegionPresenter(
            self._image_annotator.bn_drop_region_px, self._view.drop_region_view)
        self._needle_region_presenter = _ActualPresenter.DefineRegionPresenter(
            self._image_annotator.bn_needle_region_px, self._view.needle_region_view)
        self._canny_edge_detection_presenter = _ActualPresenter.CannyEdgeDetectionPresenter(
            self._image_annotator, self._view.canny_parameters_view)
        self._edge_detection_overlay_presenter = _ActualPresenter.EdgeDetectionOverlayPresenter(
            self._image_annotator, self._preview, self._view.edge_detection_overlay_view)
        self._errors_presenter = self.ErrorsPresenter(self._image_annotator.validator, self._view.errors_view)

        self.__event_connections = [
            self._drop_region_presenter.on_new_region_defined.connect(
                self._hdl_drop_region_presenter_new_region_defined),
            self._needle_region_presenter.on_new_region_defined.connect(
                self._hdl_needle_region_presenter_new_region_defined)
        ]

        self.__data_bindings = [
            Binding(self._preview.bn_image, self._view.image_acquisition_preview_view.bn_image),
        ]

        if self._image_annotator.bn_drop_region_px.get() is None:
            self._view.bn_define_region_mode.set(_ActualView.DefineRegionMode.DROP)
        elif self._image_annotator.bn_needle_region_px.get() is None:
            self._view.bn_define_region_mode.set(_ActualView.DefineRegionMode.NEEDLE)
        else:
            self._view.bn_define_region_mode.set(_ActualView.DefineRegionMode.NONE)

    def _hdl_drop_region_presenter_new_region_defined(self) -> None:
        if self._image_annotator.bn_needle_region_px.get() is None:
            self._view.bn_define_region_mode.set(_ActualView.DefineRegionMode.NEEDLE)
        else:
            self._view.bn_define_region_mode.set(_ActualView.DefineRegionMode.NONE)

    def _hdl_needle_region_presenter_new_region_defined(self) -> None:
        self._view.bn_define_region_mode.set(_ActualView.DefineRegionMode.NONE)

    def destroy(self) -> None:
        if self._preview_config_presenter is not None:
            self._preview_config_presenter.destroy()

        self._drop_region_presenter.destroy()
        self._needle_region_presenter.destroy()
        self._edge_detection_overlay_presenter.destroy()
        self._canny_edge_detection_presenter.destroy()
        self._errors_presenter.destroy()

        for ec in self.__event_connections:
            ec.disconnect()

        for db in self.__data_bindings:
            db.unbind()


class IFTImageProcessingFormPresenter:
    def __init__(self, image_annotator: IFTImageAnnotator,
                 create_image_acquisition_preview: Callable[[], Optional[ImageAcquisitionPreview]],
                 view: IFTImageProcessingFormView) -> None:
        self._image_annotator = image_annotator
        self._create_image_acquisition_preview = create_image_acquisition_preview

        self._enabled = False
        self._destroyed = False

        self._container_view = view
        self._container_model = StackModel()
        self._container_presenter = None  # type: Optional[StackPresenter]

        self._image_processing_view = _ActualView()
        self._image_processing_presenter = None  # type: Optional[_ActualPresenter]
        self._container_model.add_child(self._image_processing_view, self._image_processing_view)

        self._no_preview_view = MessageTextView('Failed to create image acquisition preview.')
        self._container_model.add_child(self._no_preview_view, self._no_preview_view)

    def validate(self) -> bool:
        is_valid = self._image_annotator.validator.check_is_valid()
        self._image_processing_view.errors_view.touch_all()
        return is_valid

    def enter(self) -> None:
        if self._enabled or self._destroyed:
            return

        self._container_presenter = StackPresenter(self._container_model, self._container_view)

        preview = self._create_image_acquisition_preview()
        if preview is None:
            # Make error message view visible
            self._container_model.visible_child_key = self._no_preview_view
            self._enabled = True
            return

        self._image_processing_presenter = _ActualPresenter(
            self._image_annotator, preview, self._image_processing_view)

        # Make image processing view visible
        self._container_model.visible_child_key = self._image_processing_view
        self._enabled = True

    def leave(self) -> None:
        if not self._enabled or self._destroyed:
            return

        self._container_presenter.destroy()

        if self._image_processing_presenter is not None:
            self._image_processing_presenter.destroy()
            self._image_processing_presenter = None

        self._enabled = False

    def destroy(self) -> None:
        assert not self._destroyed

        if self._enabled:
            self.leave()

        self._destroyed = True
