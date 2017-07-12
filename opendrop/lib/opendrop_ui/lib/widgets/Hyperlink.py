from opendrop.shims import tkinter_ as tk
import tkFont
import webbrowser

class Hyperlink(tk.Label, object):
    def __init__(self, *args, **kwargs):
        url = ""

        if "url" in kwargs:
            url = kwargs["url"]
            del kwargs["url"]
        elif "text" in kwargs:
            url = kwargs["text"]

        font = tkFont.Font(family = "TkDefaultFont", size = 9)

        if "font" in kwargs:
            font = kwargs["font"]
        else:
            kwargs["font"] = font

        kwargs["cursor"] = "arrow"

        super(Hyperlink, self).__init__(*args, **kwargs)

        font_active = tkFont.Font(font = font)
        font_active.config(underline = True)
        fg_active = "blue"

        font_inactive = tkFont.Font(font = font)
        font_inactive.config(underline = False)
        fg_inactive = self.cget("fg")

        self.bind("<Button-1>", hotlink_url_callback(url))
        self.bind("<Enter>", lambda e: self.configure(font = font_active, fg = fg_active))
        self.bind("<Leave>", lambda e: self.configure(font = font_inactive, fg = fg_inactive))

def hotlink_url_callback(url):
    """
    Creates a callback that opens a url when called

    Args:
        url(str): url that the browser should open when called
    Returns:
        A callback function that takes any number of arguments but will always open the given
        url when called
    """
    def cb(*args, **kwargs):
        webbrowser.open_new(url)

    return cb
