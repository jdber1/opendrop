from opendrop.constants import ImageSourceOption

from opendrop.opendrop_ui import widgets
from opendrop.opendrop_ui.view_manager import View

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

def calculate_scale(rel_size, mins, maxs):
    scale = 1

    if rel_size.x < mins.x or rel_size.y < mins.y:
        scale *= max(mins.x/rel_size.x, mins.y/rel_size.y)

    rel_size *= scale

    if rel_size.x > maxs.x or rel_size.y > maxs.y:
        scale *= min(maxs.x/rel_size.x, maxs.y/rel_size.y)

    return scale

class SelectRegion(View):
    def submit(self):
        region = self.selector.value

        if not region.size == (0, 0):
            region = (region / self.scale).round_to_int()

            self.events.submit(region)

    def cancel(self):
        self.events.submit(None)

    @coroutines.co
    def image_source_fetch_loop(self):
        for timestamp, image, wait_lock in self.image_source.frames():
            with self.busy:
                if not self.alive: break
                resized_image = image.resize(self.resize_to, resample=Image.BILINEAR)
                image_tk = ImageTk.PhotoImage(resized_image)

                # Not entirely sure if this part is necessary
                image.close()
                resized_image.close()

                self.selector.configure(image=image_tk)

                yield wait_lock(min_wait = 1.0/24)

    def body(self, image_source_desc, image_source_type):
        root = self.root

        if image_source_type == ImageSourceOption.LOCAL_IMAGES:
            # If just images, then cycle through them at a framerate of 2fps (interval=0.5)
            self.image_source = source_loader.load(image_source_desc, image_source_type,
                                                   interval = 0.5, loop=True)
        elif image_source_type == ImageSourceOption.USB_CAMERA:
            self.image_source = source_loader.load(image_source_desc, image_source_type)
        elif image_source_type == ImageSourceOption.FLEA3:
            raise NotImplementedError

        screen_res = self.view_manager.screen_resolution
        image_source_size = self.image_source.size
        image_source_rel_size = Vector2(
            float(image_source_size.x)/screen_res.x,
            float(image_source_size.y)/screen_res.y
        )

        self.scale = calculate_scale(image_source_rel_size, REL_SIZE_MIN, REL_SIZE_MAX)
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

        self.image_source_fetch_loop()

    def _clear(self):
        self.image_source.release()

    def refresh(self):
        self.selector.value = BBox2()
