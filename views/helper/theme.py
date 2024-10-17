from customtkinter import *

DARK_MODE = "Dark"
LIGHT_MODE = "Light"

def get_system_text_color():
    if get_appearance_mode() == DARK_MODE:
        return 'white'
    else:
        return 'black'
