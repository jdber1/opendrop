import os
import copy

from opendrop.shims import tkinter_ as tk
import tkFileDialog, tkSimpleDialog
from opendrop.shims import ttk_ as ttk
import tkFont

from opendrop.opendrop_ui.view_manager import View
from opendrop.opendrop_ui import widgets

from opendrop.constants import ImageSourceOption

# UI parameter tweaks

BACKGROUND_COLOR = "gray90"

FONT = ("Helvetica", 10)

NEEDLE_OPTIONS = ["0.7176", "1.270", "1.651"]

PATH_TO_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "opendrop_parameters.csv")

LABEL_WIDTH = 29
ENTRY_WIDTH = 11

# End of tweaks

widgets = widgets.preconfigure({
    "*": {
        "background": BACKGROUND_COLOR,
    },
    "Label": {
        "font": FONT
    },
    "Hyperlink": {
        "font": FONT
    },
    "forms": {
        "*": {
            "font": FONT
        },
        "LabelFrame": {
            "padx": 30,
            "pady": 10
        },
        "FloatEntry": {
            "width": ENTRY_WIDTH
        },
        "FloatCombobox": {
            "width": ENTRY_WIDTH
        },
    },
    "button": {
        "highlightbackground": BACKGROUND_COLOR
    }
})

class OpendropUserInput(View):
    def image_source_change(self, self_, val):
        if val == "Local images":
            self.save_images_checkbutton.disable()
        elif self.save_images_checkbutton.state == "disabled":
            self.save_images_checkbutton.normal()

    def submit(self):

        # TODO: Export preferences

        if self.image_source_type.value == ImageSourceOption.LOCAL_IMAGES:
            image_source = tkFileDialog.askopenfilenames(
                parent = self.root,
                title = "Select files",
                initialdir = os.getcwd()
            )

            if len(image_source) == 0:
                # Cancel operation
                return

            # Sort the input files in lexicographic order
            image_source = sorted(image_source)

            self.image_source.value = image_source
            self.num_frames.value = len(image_source)
        elif self.image_source_type.value == ImageSourceOption.USB_CAMERA:
            image_source = tkSimpleDialog.askinteger(
                parent = self.root,
                title = "USB Camera",
                prompt = "Camera index",
                initialvalue = 0
            )

            if image_source is None:
                # Cancel operation
                return

            self.image_source.value = image_source

        self.events.submit.fire(self.form.submit())

    def cancel(self):
        self.events.submit.fire(None)

    def restore_form(self, data):
        self.form.update(data)

    def body(self):
        root = self.root

        root.geometry("650x550")

        root.configure(background = BACKGROUND_COLOR, padx = 50)

        form = widgets.forms.Frame(root)
        form.pack()

        form.columnconfigure(0, weight = 1)
        form.columnconfigure(1, weight = 1)

        self.form = form

        # Title banner

        title_frame = tk.Frame(form)
        title_frame.grid(row = 0, columnspan = 2, rowspan = 1, padx = 30, pady = 10)

        tk.Label(title_frame,
            text = "Open drop",
            background = BACKGROUND_COLOR,
            font = ("Helvetica", 36),
            anchor = "center"
        ).grid(row = 0)

        # Physical inputs

        #---- Physical inputs Frame

        physical_frame = widgets.forms.LabelFrame(form,
            text = "Physical inputs",
            name = "physical_inputs"
        )
        physical_frame.grid(row = 1, column = 0, columnspan = 1, sticky = "wens", padx = 15,
                            pady = 15)

        #-------- Drop density FloatEntry

        widgets.Label(physical_frame, text = "Drop density (kg/m"u"\u00b3""):") \
            .grid(row = 0, column = 0, sticky = "w")
        widgets.forms.FloatEntry(physical_frame,
            name = "density_inner"
        ).grid(row = 0, column = 1, sticky = "we")

        #-------- Continuous density FloatEntry

        widgets.Label(physical_frame, text = "Continuous density (kg/m"u"\u00b3""):") \
            .grid(row = 1, column = 0, sticky = "w")
        widgets.forms.FloatEntry(physical_frame,
            name = "density_outer"
        ).grid(row = 1, column = 1, sticky = "we")

        #-------- Needle diameter FloatCombobox

        widgets.Label(physical_frame, text = "Needle diameter (mm):") \
            .grid(row = 2, column = 0, sticky = "w")
        widgets.forms.FloatCombobox(physical_frame,
            values = NEEDLE_OPTIONS,
            name = "needle_diameter"
        ).grid(row = 2, column = 1, sticky = "we")

        #-------- Threshold value FloatEntry

        widgets.Label(physical_frame, text = "Threshold value:") \
            .grid(row = 3, column = 0, sticky = "w")
        widgets.forms.FloatEntry(physical_frame,
            name = "threshold_val"
        ).grid(row = 3, column = 1, sticky = "we")

        # Plotting checklist

        #---- Plotting checklist frame

        pclist_frame = widgets.forms.LabelFrame(form,
            text = "To view during fitting",
            name = "plotting_checklist"
        )
        pclist_frame.grid(row = 1, column = 1, columnspan = 1, sticky = "wens", padx = 15,
                          pady = 15)

        #-------- Checkbuttons, Residuals, Profiles, Physical quantities

        widgets.forms.Checkbutton(pclist_frame, text = "Residuals", name = "residuals_boole") \
            .grid(row = 0, column = 0, pady = 2, sticky = "w")
        widgets.forms.Checkbutton(pclist_frame, text = "Profiles", name = "profiles_boole") \
            .grid(row = 1, column = 0, pady = 2, sticky = "w")
        widgets.forms.Checkbutton(pclist_frame, text = "Physical quantities", name = "IFT_boole") \
            .grid(row = 2, column = 0, pady = 2, sticky = "w")

        # Save location

        #---- Save location frame

        location_frame = widgets.forms.LabelFrame(form,
            text = "Output data location",
            name = "save_location"
        )
        location_frame.grid(row = 2, columnspan = 2, rowspan = 1, sticky = "we", padx = 15, pady = 10)
        location_frame.columnconfigure(1, weight = 1)

        #-------- Directory entry

        widgets.Label(location_frame, text = "Location:") \
            .grid(row = 0, column = 0, sticky = "w")
        widgets.forms.DirectoryEntry(location_frame,
            name = "directory"
        ).grid(row = 0, column = 1, columnspan = 3, sticky = "we")

        #-------- Filename entry

        widgets.Label(location_frame, text = "Filename:") \
            .grid(row = 1, column = 0, sticky = "w")
        widgets.forms.TextEntry(location_frame,
            name = "filename"
        ).grid(row = 1, column = 1, sticky = "we")

        #------------ Filename extension label

        widgets.Label(location_frame, text = "[YYYY-MM-DD-hhmmss].[ext]") \
            .grid(row = 1, column = 2, columnspan = 2, sticky = "e")

        # Image acquisition

        #---- Image acquisition frame

        image_acquisition_frame = widgets.forms.LabelFrame(form,
            text = "Image acquisition",
            name = "image_acquisition"
        )
        image_acquisition_frame.grid(row = 3, columnspan = 3, rowspan = 1, sticky = "we",
                                     padx = 15, pady = 10)
        image_acquisition_frame.columnconfigure(2, weight = 1)

        #-------- Source option menu

        widgets.Label(image_acquisition_frame, text = "Image source:", width = 12) \
            .grid(row = 0, column = 0, sticky = "w")
        self.image_source_type = widgets.forms.OptionMenu(image_acquisition_frame,
            name = "image_source_type",
            values = ImageSourceOption,
            width = "15"
        )
        self.image_source_type.on_change.bind(self.image_source_change)

        self.image_source_type.grid(row = 0, column = 1, sticky = "w")

        #-------- Hidden value for selected files

        self.image_source = widgets.forms.Value(image_acquisition_frame, name = "image_source")

        #-------- Number of frames

        widgets.Label(image_acquisition_frame, text = "Number of frames:") \
            .grid(row = 3, column = 0, sticky = "w")
        self.num_frames = widgets.forms.IntegerEntry(image_acquisition_frame,
            name = "num_frames",
            width = 10
        )
        self.num_frames.grid(row = 3, column = 1, padx = 10, sticky = "we")

        #-------- Wait time

        widgets.Label(image_acquisition_frame, text = "Wait time (s):") \
            .grid(row = 4, column = 0, sticky = "w")
        widgets.forms.IntegerEntry(image_acquisition_frame,
            name = "wait_time",
            width = 10
        ).grid(row = 4, column = 1, padx = 10, sticky = "we")

        #-------- Checkbuttons, Save image, Create new directory

        self.save_images_checkbutton = widgets.forms.Checkbutton(image_acquisition_frame,
            text = "Save image",
            name = "save_images"
        )
        self.save_images_checkbutton.grid(row = 3, column = 3, pady = 2, sticky = "w")

        def save_images_checkbutton_change(self_, val):
            if val:
                self.create_new_dir_checkbutton.normal()
            else:
                self.create_new_dir_checkbutton.disable()

        self.save_images_checkbutton.on_change.bind(save_images_checkbutton_change)

        self.create_new_dir_checkbutton = widgets.forms.Checkbutton(image_acquisition_frame,
            text = "Create new directory",
            name = "create_new_dir"
        )
        self.create_new_dir_checkbutton.grid(row = 4, column = 3, pady = 2, sticky = "w")

        # Just to give image_source default value and trigger its on_change event to update the
        # 'Save images' and 'Create new directiory' checkbuttons
        self.image_source_type.value = self.image_source_type.values[0]

        # Run/Quit buttons

        run_quit_frame = widgets.Frame(root)
        run_quit_frame.pack(padx = 10, pady = 10, fill = "both") #grid(row = 4, column = 0, columnspan = 2, padx = 10, pady = 10, sticky = "we")
        run_quit_frame.columnconfigure(0, weight = 1)
        run_quit_frame.columnconfigure(1, weight = 1)

        quit_button = widgets.Button(run_quit_frame,
            text = "Cancel",
            command = self.cancel
        )
        quit_button.grid(row = 0, column = 0)

        run_button = widgets.Button(run_quit_frame,
            text = "Run",
            command = self.submit
        )
        run_button.grid(row = 0, column = 1)

        root.bind("<Return>", lambda _: self.submit())
        root.bind("<Escape>", lambda _: self.cancel())

        # Homepage url Hyperlink

        footer_frame = widgets.Frame(root)
        footer_frame.pack(padx = 10, pady = 10, fill = "both")

        widgets.Hyperlink(footer_frame,
            text = "opencolloids.com",
            url = "http://www.opencolloids.com"
        ).pack(anchor = "e") #pack() #(x = 40, y = 10)

        self.center()
