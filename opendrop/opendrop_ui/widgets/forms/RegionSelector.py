from FormWidget import FormWidget

from opendrop.shims import tkinter_ as tk

from opendrop.utility.argfiddler import ExtKwargs
from opendrop.utility.events import Event
from opendrop.utility.vectors import Vector2, BBox2

class RegionSelector(FormWidget, tk.Canvas):
    def __init__(self, master, size, name=None, scale=1, **options):
        FormWidget.__init__(self, master, name)

        tk.Canvas.__init__(self, master,
            width=size.x,
            height=size.y
        )

        self.value = BBox2()

        self.image = self.create_image((0, 0), anchor = "nw")

        self.box = self.create_rectangle(self.value.to_4tuple(), state=tk.HIDDEN)
        self.box_conf = {"box_border": "black"}

        self.down_at = Vector2()

        self.bind("<Button-1>", lambda e: self.button1_down(e.x, e.y))
        self.bind("<B1-Motion>", lambda e: self.button1_move(e.x, e.y))
        self.bind("<ButtonRelease-1>", lambda e: self.button1_up(e.x, e.y))

        self.on_change.bind(lambda v: self.redraw_box())

        self.configure(**options)

    def button1_down(self, x, y):
        if "box_active_border" in self.box_conf:
            self.configure(_box_border = self.box_conf["box_active_border"])

        self.down_at = Vector2(x, y)
        self.value = BBox2(position = self.down_at, size=(0, 0))

    def button1_move(self, x, y):
        x = min(max(x, 0), self.winfo_width())
        y = min(max(y, 0), self.winfo_height())

        self.value = BBox2(self.down_at, (x, y))

    def button1_up(self, x, y):
        self.configure(_box_border = self.box_conf["box_border"])

        if self.value.size == (0, 0):
            self.itemconfig(self.box, state=tk.HIDDEN)

    def redraw_box(self):
        if self.itemconfig(self.box)["state"][-1] == tk.HIDDEN:
            self.itemconfig(self.box, state=tk.NORMAL)

        self.coords(self.box, self.value.to_4tuple())

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if not hasattr(self, "on_change"):
            self.on_change = Event()

        self._value = new_value
        self.on_change.fire(new_value)

    def configure(self, **options):
        options = ExtKwargs(options).alias({"background": "bg", "box_border": "box_bd",
                                            "box_active_border": "box_active_bd",
                                            "box_border_width": "box_bd_width",
                                            "_box_border": "_box_bd"})

        box_conf_options = options.extract("box_border", "box_active_border")

        if "box_border" in box_conf_options:
            self.box_conf["box_border"] = box_conf_options["box_border"]
        if "box_active_border" in box_conf_options:
            self.box_conf["box_active_border"] = box_conf_options["box_active_border"]

        canvas_options = ExtKwargs(options).extract("width", "height", "cursor", "background", "window")
        tk.Canvas.configure(self, **canvas_options)

        box_options = options.extract("_box_border", "box_border", "box_border_width") \
                             .rename({"_box_border": "outline", "box_border": "outline",
                                      "box_border_width": "width"})
        self.itemconfigure(self.box, **box_options)

        image_options = options.extract("image")
        self.itemconfigure(self.image, **image_options)

        if "image" in image_options:
            # Keep a reference to the new image
            self.image_ref = image_options["image"]
