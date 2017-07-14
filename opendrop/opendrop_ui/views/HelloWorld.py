from opendrop.opendrop_ui.view_manager import View
from opendrop.opendrop_ui import widgets

class HelloWorld(View):
    def body(self):
        root = self.root

        root.geometry("200x100")

        self.center()

        widgets.Label(text = "Hello, world", font = ("Helvetica", "16"), background = "white") \
            .pack(expand = True, fill = "both")
