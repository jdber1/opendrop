from opendrop.constants import ImageSourceOption

from opendrop.opendrop_ui import widgets
from opendrop.opendrop_ui.view_manager import View
from opendrop.opendrop_ui.views.utility.scale_from_bounds import scale_from_bounds

from opendrop.resources import resources

from opendrop.shims import tkinter_ as tk

import opendrop.utility.coroutines as coroutines
import opendrop.utility.source_loader as source_loader
from opendrop.utility.vectors import Vector2

from PIL import Image, ImageTk

import threading, time

widgets = widgets.preconfigure({
    "forms": {
        "RegionSelector": {
            "box_bd": "#00ff7f",
            "box_active_bd": "#ff4040",
            "box_bd_width": 2,
        }
    }
})

WIDTH_MIN, WIDTH_MAX = 0.4, 0.5
HEIGHT_MIN, HEIGHT_MAX = 0.4, 0.5

REL_SIZE_MIN = Vector2(WIDTH_MIN, HEIGHT_MIN)
REL_SIZE_MAX = Vector2(WIDTH_MAX, HEIGHT_MAX)

class SelectRegion(View):
    def submit(self):
        region = self.selector.value

        if not region.size == (0, 0):
            region = (region / self.scale).round_to_int()

            self.events.submit(region)

    def cancel(self):
        self.events.submit(None)

    @coroutines.co
    def update_image(self, image):
        with self.busy:
            if not self.alive:
                self.update_image_bind.unbind()
                return

            if image:
                resized_image = image.resize(self.resize_to, resample=Image.BILINEAR)
                image_tk = ImageTk.PhotoImage(resized_image)

                # Not entirely sure if this part is necessary
                image.close()
                resized_image.close()

                self.selector.configure(image=image_tk)


    def body(self, image_source_desc, image_source_type):
        root = self.root

        with self.busy:
            image_source_fps = None

            if image_source_type == ImageSourceOption.LOCAL_IMAGES:
                # If just images, then cycle through them at a framerate of 2fps
                self.image_source = source_loader.load(image_source_desc, image_source_type)
                image_source_fps = 2
            elif image_source_type == ImageSourceOption.USB_CAMERA:
                self.image_source = source_loader.load(image_source_desc, image_source_type)
                image_source_fps = None # None specifies as fast as possible
            elif image_source_type == ImageSourceOption.FLEA3:
                raise NotImplementedError("Flea3 not supported yet")

            screen_res = self.view_manager.screen_resolution
            image_source_size = self.image_source.size

            self.scale = scale_from_bounds(
                image_size=image_source_size,
                max_size=REL_SIZE_MAX * screen_res,
                min_size=REL_SIZE_MIN * screen_res
            )

            self.resize_to = (image_source_size * self.scale).round_to_int()

            # Widgets

            self.selector = widgets.forms.RegionSelector(root, size = self.resize_to)
            self.selector.pack()

        # Resizing and recentering root

        root.geometry("{0}x{1}".format(*self.resize_to))
        self.center()

        # Root event bindings

        root.bind("<space>", lambda e: self.submit())
        root.bind("<Return>", lambda e: self.submit())

        root.bind("<Escape>", lambda e: self.cancel())

        # Background tasks

        self.update_image_bind = self.image_source.playback(
            fps=image_source_fps,
            loop=True
        ).bind(self.update_image)

    def _clear(self):
        self.image_source.release()

    def refresh(self):
        self.selector.value = BBox2()
