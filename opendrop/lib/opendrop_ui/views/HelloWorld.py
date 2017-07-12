from opendrop.lib.opendrop_ui.lib.view_manager import View
from opendrop.lib.opendrop_ui.lib import widgets

class HelloWorld(View):
    def body(self):
        root = self.root

        root.geometry("200x100")

        self.center()

        widgets.Label(text = "Hello, world", font = ("Helvetica", "16"), background = "white") \
            .pack(expand = True, fill = "both")
