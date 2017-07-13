from opendrop.shims import tkinter_ as tk
import tkFont
from PIL import Image, ImageTk

from opendrop.opendrop_ui.view_manager import View
from opendrop.opendrop_ui import widgets

from opendrop.resources import resources
from opendrop.constants import OperationMode

class MainMenu(View):
    def submit(self, operation_mode):
        self.events.submit(operation_mode)

    def body(self):
        root = self.root

        root.geometry("550x550")

        root.configure(padx = 0, pady = 0)

        self.center()

        logo_image = ImageTk.PhotoImage(Image.open(resources("images/logo/logo.png")))

        logo = tk.Label(root, image = logo_image, width = 250, height = 333)
        logo.image = logo_image
        logo.pack(side = "left", anchor = "n", padx = 10, pady = 10)

        gpl_link = widgets.Hyperlink(root, text = "under GPl license",
                                     url = r"http://www.gnu.org/copyleft/gpl.html",
                                     font = tkFont.Font(size = 9))
        gpl_link.pack(side = "left", anchor = "s", pady = 10, fill = None, expand = None)

        # Create program mode buttons
        #---- Create first group's frame, opendrop

        frame1_labeltext = "opendrop:"

        frame1 = tk.Frame(root, bd = 20, highlightbackground = "black", highlightcolor = "black",
                           highlightthickness = 1, width = 150, height = 280)
        frame1.propagate(0)
        frame1.pack(side = "top", anchor = "e")
        labelDrop = tk.Label(frame1, text = frame1_labeltext)
        labelDrop.pack(side = "top", anchor = "w")

        #-------- Group 1, Mode 1, pendantDrop

        button1_image = ImageTk.PhotoImage(Image.open(resources("images/buttons/pendant.png")))
        button1_labeltext = "pendantDrop"
        button1_command = lambda: self.submit(OperationMode.PENDANT)

        button1 = tk.Button(frame1, image = button1_image, width = 50, height = 61,
                            command = button1_command)
        button1.image = button1_image
        button1.pack(side = "top", anchor = "e", padx = 10, pady = 10)

        label1 = tk.Label(frame1, text = button1_labeltext)
        label1.pack(side = "top", anchor = "e")

        #-------- Group 1, Mode 2, sessileDrop

        button2_image = ImageTk.PhotoImage(Image.open(resources("images/buttons/sessile.png")))
        button2_labeltext = "sessileDrop"
        button2_command = lambda: self.submit(OperationMode.SESSILE)

        button2 = tk.Button(frame1, image = button2_image, width = 50, height = 61,
                            command = button2_command)
        button2.image = button2_image
        button2.pack(side = "top", anchor = "e", padx = 10, pady = 10)

        label2 = tk.Label(frame1, text = button2_labeltext)
        label2.pack(side = "top", anchor = "e")

        #---- Second group, contactAn

        frame2_labeltext = "contactAn:"

        frame2 = tk.Frame(root, bd = 20, highlightbackground = "black", highlightcolor = "black",
                          highlightthickness = 1, width = 150, height = 280)
        frame2.pack(side = "top", anchor = "e")
        frame2.propagate(0)
        labelConAn = tk.Label(frame2, text = frame2_labeltext)
        labelConAn.pack(side = "top", anchor = "w")

        #-------- Group 2, Mode 3, contactAngle

        button3_image = ImageTk.PhotoImage(Image.open(resources("images/buttons/contact.png")))
        button3_labeltext = "contactAngle"
        button3_command = lambda: self.submit(OperationMode.CONAN)

        button3 = tk.Button(frame2, image = button3_image, width = 50, height = 61,
                            command = button3_command)
        button3.image = button3_image
        button3.pack(side = "top", anchor = "e", padx = 10, pady = 10)

        label3 = tk.Label(frame2, text = button3_labeltext)
        label3.pack(side = "top", anchor = "e")

        #-------- Group 2, Mode 4, conAn-needle

        button4_image = ImageTk.PhotoImage(Image.open(resources("images/buttons/needle.png")))
        button4_labeltext = "conAn-needle"
        button4_command = lambda: self.submit(OperationMode.CONAN_NEEDLE)

        button4 = tk.Button(frame2, image = button4_image, width = 50, height = 61,
                            command = button4_command)
        button4.image = button4_image
        button4.pack(side = "top", anchor = "e", padx = 10, pady = 10)

        label4 = tk.Label(frame2, text=button4_labeltext)
        label4.pack(side = "top", anchor = "e")
