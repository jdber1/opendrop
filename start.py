import Tkinter # import the Tkinter module
import opendrop
from PIL import Image, ImageTk
import contact_angle

import webbrowser

def pendantDrop(root):
    root.destroy()
    opendrop.opendrop(1,None)


def sessileDrop(root):
    root.destroy()
    opendrop.opendrop(2,None)


def contactAngle(root):
    root.destroy()
    contact_angle.contactAngle(1,None)


def contactAngleNeedle(root):
    root.destroy()
    contact_angle.contactAngle(2,None)


def main():
    root = Tkinter.Tk() # create a root window
    root.title('Version2.0')
    root.geometry('550x550+300+50')

    logoPhoto = ImageTk.PhotoImage(Image.open("images/logo.png"))
    pendant = ImageTk.PhotoImage(Image.open("images/pendant.png"))
    sessile = ImageTk.PhotoImage(Image.open("images/sessile.png"))
    contact = ImageTk.PhotoImage(Image.open("images/contact.png"))
    contact_needle = ImageTk.PhotoImage(Image.open("images/needle.png"))

    logo = Tkinter.Label(root, image=logoPhoto, width=250, height=333)
    logo.pack(side="left", anchor='n', padx=10, pady=10)

    text_gpl = Tkinter.Label(root, text="under GPl license\n")
    text_gpl.pack(side='left', anchor='s', fill=None, expand=None)
    text_gpl.bind("<Button-1>", gpl_url_callback)


    frame1 = Tkinter.Frame()
    frame1 = Tkinter.Frame(bd=20, highlightbackground="black", highlightcolor="black", highlightthickness=1,
                           width=150, height=280)
    frame1.propagate(0)
    frame1.pack(side="top", anchor='e')
    labelDrop = Tkinter.Label(frame1, text='opendrop:')
    labelDrop.pack(side="top", anchor="w")
    button1 = Tkinter.Button(frame1, image=pendant, command=lambda: pendantDrop(root), width=50, height=61)
    button1.pack(side="top", anchor="e", padx=10, pady=10)
    label1 = Tkinter.Label(frame1, text='pendantDrop')
    label1.pack(side='top', anchor="e")
    button2 = Tkinter.Button(frame1, image=sessile, command=lambda: sessileDrop(root), width=50, height=61)
    button2.pack(side="top", anchor="e", padx=10, pady=10)
    label2 = Tkinter.Label(frame1, text='sessileDrop')
    label2.pack(side='top', anchor="e")
    frame2 = Tkinter.Frame(root, bd=20, highlightbackground="black", highlightcolor="black", highlightthickness=1,
                           width=150, height=280)
    frame2.pack(side="top", anchor='e')
    frame2.propagate(0)
    labelConAn = Tkinter.Label(frame2, text='contactAn:')
    labelConAn.pack(side="top", anchor="w")
    button3 = Tkinter.Button(frame2, image=contact, command=lambda: contactAngle(root), width=50, height=61)
    button3.pack(side="top", anchor="e", padx=10, pady=10)
    label3 = Tkinter.Label(frame2, text='contactAngle')
    label3.pack(side='top', anchor="e")
    button4 = Tkinter.Button(frame2, image=contact_needle, command=lambda: contactAngleNeedle(root), width=50, height=61)
    button4.pack(side="top", anchor="e", padx=10, pady=10)
    label4 = Tkinter.Label(frame2, text='conAn-needle')
    label4.pack(side='top', anchor="e")

    root.mainloop() # create an event loop


def homepage_url_callback(self):
    webbrowser.open_new(r"http://www.opencolloids.com")
def gpl_url_callback(self):
    webbrowser.open_new(r"http://www.gnu.org/copyleft/gpl.html")

if __name__ == '__main__':
    main()