#!/usr/bin/env python
#coding=utf-8

try:
    # for Python2
    import Tkinter as tk
except ImportError:
    # for Python3
    import tkinter as tk
import tkFileDialog
import tkFont
# from ttk import *
import ttk
import webbrowser
import sys
import os
import csv

# from classes import ExperimentalSetup

IMAGE_EXTENSION='.png'

BACKGROUND_COLOR='gray90'
# BACKGROUND_COLOR='SlateGray1'
# BACKGROUND_COLOR='red'
VERSION='1.1'

NEEDLE_OPTIONS = ['0.7176', '1.270', '1.651']
IMAGE_SOURCE_OPTIONS = ["Flea3", "USB camera", "Local images"]

PATH_TO_SCRIPT = os.path.join(os.path.dirname(os.path.realpath(__file__)),'..')
PATH_TO_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)),"opendrop_parameters.csv")

# FONT_FRAME_LABEL = ("Helvetica", 16, "BOLD")
FONT_FRAME_LABEL = '*-*-medium-r-normal--*-160-*'

LABEL_WIDTH = 29
ENTRY_WIDTH = 11

# fullPathName = os.path.abspath(os.path.dirname(sys.argv[0]))
def call_user_input(user_input_data):
    UserInterface(user_input_data)

class UserInterface(tk.Toplevel):
    def __init__(self, user_input_data):
        self.initialise = True # need this flag to disable float and integer checking for inputs
        self.root = tk.Tk()
        self.root.geometry("+100+100")
        self.screen_resolution = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
        self.root.lift()
        self.root.call('wm', 'attributes', '.', '-topmost', True)
        self.root.after_idle(self.root.call, 'wm', 'attributes', '.', '-topmost', False)

        self.root.title('OpenDrop v '+VERSION)

        self.root.configure(height=25, background=BACKGROUND_COLOR, padx=50)
        self.create_title()
        self.create_physical_inputs()
        self.create_plotting_checklist()
        self.create_save_location()
        self.create_image_acquisition()
        # self.create_save_box()
        self.create_run_quit(user_input_data)
        self.create_homepage_url()

        self.import_parameters()

        self.root.config()
        self.initialise = False # need this to setup entry widgets validation
        if user_input_data.auto_test_parameters != None:
            self.run(user_input_data)
            return

        self.root.mainloop()

    def create_title(self):
        title_frame = tk.Frame(self.root)
        title_frame.config(background=BACKGROUND_COLOR)
        title_frame.grid(row=0, columnspan=3, rowspan=1, padx=30, pady=10)
        # Label(title_frame, text="Open drop", font=("Helvetica", 36), justify=CENTER, background="lavender").grid(row=0, sticky=N)
        tk.Label(title_frame, text="Open drop", background=BACKGROUND_COLOR, font=("Helvetica", 36), anchor="center").grid(row=0)

    def create_physical_inputs(self):
        physical_frame = tk.LabelFrame(self.root, text="Physical inputs", padx=30, pady=10)
        physical_frame.config(background=BACKGROUND_COLOR)
        physical_frame.grid(row=1, column=0, columnspan=2, sticky="wens", padx=15, pady=15) #, rowspan=3

        self.density_inner = FloatEntryStyle(self, physical_frame, "Drop density (kg/m"u"\u00b3""):", rw=0, width_specify=ENTRY_WIDTH) #, label_width=LABEL_WIDTH)
        self.density_outer = FloatEntryStyle(self, physical_frame, "Continuous density (kg/m"u"\u00b3""):", rw=1) #, label_width=LABEL_WIDTH)
        self.needle_diameter = FloatComboboxStyle(self, physical_frame, "Needle diameter (mm):", NEEDLE_OPTIONS, rw=2) #, label_width=LABEL_WIDTH)
        self.threshold_val = FloatEntryStyle(self, physical_frame, "Threshold value:", rw=4, width_specify=ENTRY_WIDTH)

        physical_frame.grid_columnconfigure(0, minsize=LABEL_WIDTH)

    def create_plotting_checklist(self):
        clist_frame = tk.LabelFrame(self.root, text="To view during fitting", padx=30, pady=10) #, height=15)
        clist_frame.config(background=BACKGROUND_COLOR)
        clist_frame.grid(row=1, column=2, columnspan=1, sticky="wens", padx=15, pady=15) #, rowspan=3

        self.residuals_boole = CheckButtonStyle(self, clist_frame, "Residuals", rw=0, cl=0)
        self.profiles_boole = CheckButtonStyle(self, clist_frame, "Profiles", rw=1, cl=0)
        self.IFT_boole = CheckButtonStyle(self, clist_frame, "Physical quantities", rw=2, cl=0)


    def create_image_acquisition(self):
        image_acquisition_frame = tk.LabelFrame(self.root, text="Image acquisition", height=15, padx=30, pady=10)
        image_acquisition_frame.config(background=BACKGROUND_COLOR)
        image_acquisition_frame.grid(row=5, columnspan=4, rowspan=1, sticky="we",padx=15, pady=10)
        # image_acquisition_frame.grid_columnconfigure(0, minsize=50)
        image_acquisition_frame.grid_columnconfigure(2, weight=1)

        self.image_source = OptionMenuStyle(self, image_acquisition_frame, "Image source:", IMAGE_SOURCE_OPTIONS, rw=0, label_width=12) #(LABEL_WIDTH-ENTRY_WIDTH))
        
        # self.number_frames = IntegerEntryStyle(self, image_acquisition_frame, "Number of frames:", rw=0, cl=3, pdx=10)
        # self.wait_time = IntegerEntryStyle(self, image_acquisition_frame, "Wait time (s):", rw=1, cl=3, pdx=10)

        # self.directory = DirectoryEntryStyle(self.root, self.save_info_frame, "Location:", rw=3, entry_width=50)
 
        # image_acquisition_frame.grid_columnconfigure(3, minsize=LABEL_WIDTH)
        # self.image_source.text_variable.trace_variable('w',self.propogate_state)
        self.image_source.text_variable.trace_variable('w',self.propogate_state)

        

        self.number_frames = IntegerEntryStyle(self, image_acquisition_frame, "Number of frames:", rw=3, cl=0, pdx=10)
        self.wait_time = IntegerEntryStyle(self, image_acquisition_frame, "Wait time (s):", rw=4, cl=0, pdx=10)

        self.save_images_boole = CheckButtonStyle(self, image_acquisition_frame, "Save image", rw=3, cl=3)
        self.create_new_dir_boole = CheckButtonStyle(self, image_acquisition_frame, "Create new directory", rw=4, cl=3)#, pdx=50)
        self.save_images_boole.int_variable.trace_variable('w',self.check_button_changed)



    def propogate_state(self, *args):
        if self.image_source.get_value()=="Local images":
            self.save_images_boole.disable()
            self.create_new_dir_boole.disable()
            # self.filename_string.disable()
            # self.directory.disable()
            # self.filename_extension.config(state="disable")
        else:
            self.save_images_boole.normal()
            self.check_button_changed()


    def create_save_location(self):
        location_frame = tk.LabelFrame(self.root, text="Output data location", height=15, padx=30, pady=10)
        location_frame.config(background=BACKGROUND_COLOR)
        location_frame.grid(row=4, columnspan=3, rowspan=1, sticky="w", padx=15, pady=10)
        
        self.directory = DirectoryEntryStyle(self.root, location_frame, "Location:", rw=0, entry_width=50)

        self.filename_string = TextEntryStyle(self, location_frame, "Filename:", rw=1, width_specify=20, stckyE="ew")
        self.filename_extension = tk.Label(location_frame, text="[YYYY-MM-DD-hhmmss].[ext]", background=BACKGROUND_COLOR)
        self.filename_extension.grid(row=1, column=2, columnspan=2, sticky="w")
        location_frame.columnconfigure(1,weight=1)


        

    # def create_save_box(self):
    #     self.save_info_frame = tk.LabelFrame(self.root, text="Save images", height=15, padx=30, pady=10)
    #     self.save_info_frame.config(background=BACKGROUND_COLOR)
    #     self.save_info_frame.grid(row=6, columnspan=4, rowspan=4, sticky="w", padx=15, pady=10)
    #     self.save_images_boole = CheckButtonStyle(self, self.save_info_frame, "Save image", rw=0)
    #     self.create_new_dir_boole = CheckButtonStyle(self, self.save_info_frame, "Create new directory", rw=0, cl=3, pdx=50)


    #     # self, parent, frame, text_left, rw=0, cl=0, width_specify=10, pdx=0, pdy=2, stcky="w")


    #     # self.filename_string = TextEntryStyle(self, self.save_info_frame, "Filename:", rw=2, width_specify=20, stckyE="ew")
    #     # self.filename_string.default_string = "Extracted_data"
    #     # self.filename_extension = tk.Label(self.save_info_frame, text="[YYYY-MM-DD-hhmmss]"+IMAGE_EXTENSION, background=BACKGROUND_COLOR)
    #     # self.filename_extension.grid(row=2, column=2, sticky="w")
    #     # self.save_info_frame.columnconfigure(1,weight=1)

    #     # self.directory = DirectoryEntryStyle(self.root, self.save_info_frame, "Location:", rw=3, entry_width=50)

    #     self.save_info_frame.columnconfigure(0, weight=1)
    #     self.save_info_frame.columnconfigure(1, weight=1)
    #     # self.save_info_frame.columnconfigure(4, weight=1)

    #     self.save_images_boole.int_variable.trace_variable('w',self.check_button_changed)



    def check_button_changed(self, *args):
        if self.save_images_boole.get_value():
            self.create_new_dir_boole.normal()
            # self.filename_string.normal()
            # self.directory.normal()
            # self.filename_extension.config(state="normal")
        else:
            self.create_new_dir_boole.disable()
            # self.filename_string.disable()
            # self.directory.disable()
            # self.filename_extension.config(state="disable")

        

    # def update_directory(self):
    #     directory = os.path.dirname(os.path.realpath(__file__))
    #     self.output_location_string = tkFileDialog.askdirectory(parent = self.root, title="Select output data location", initialdir=directory)
    #     self.output_location_text.config(text = self.clip_dir(self.output_location_string))


    # def clip_dir(self, string):
    #     MAX_DIR_LEN=20
    #     if len(string) > MAX_DIR_LEN:
    #         return "..." + string[-(MAX_DIR_LEN+3):]
    #     else:
    #         return string
    #     # return string


    def create_run_quit(self, user_input_data):
        # run_quit_frame = LabelFrame(self.root, text="ys", height=15)
        run_quit_frame = tk.Frame(self.root)
        run_quit_frame.config(background=BACKGROUND_COLOR)
        run_quit_frame.grid(row=22, columnspan=5, padx=10, pady=10, sticky="we")
        # save_images_run = tk.Button(run_quit_frame, text='Run', highlightbackground=BACKGROUND_COLOR, command=self.run) # , state='disabled'
        save_images_run = tk.Button(run_quit_frame, text='Run', highlightbackground=BACKGROUND_COLOR,
                                    command=lambda: self.run(user_input_data)) # , state='disabled'
        save_images_quit = tk.Button(run_quit_frame, text='Quit', highlightbackground=BACKGROUND_COLOR, command=self.quit)

        # self.root.bind("<Return>", lambda _: self.callback_run(user_input_data))
        # self.root.bind("<Escape>", self.callback_quit)
        self.root.bind("<Return>", lambda _: self.run(user_input_data))
        self.root.bind("<Escape>", lambda _: self.quit())


        run_quit_frame.columnconfigure(0, weight=1)
        run_quit_frame.columnconfigure(2, weight=1)
        run_quit_frame.columnconfigure(4, weight=1)


        # save_images_run.grid(row=0, column=1, sticky="we")#padx=15, pady=10, sticky=W+E)
        # save_images_quit.grid(row=0, column=3, sticky="we")#padx=15, pady=10, sticky=W+E)
        save_images_quit.grid(row=0, column=1, sticky="we")#padx=15, pady=10, sticky=W+E)
        save_images_run.grid(row=0, column=3, sticky="we")#padx=15, pady=10, sticky=W+E)
    

    def create_homepage_url(self):
        homepage_frame = tk.Frame(self.root)
        homepage_frame.config(background=BACKGROUND_COLOR)
        homepage_frame.grid(row=23, columnspan=4, padx=40, pady=10, sticky="e")

        self.label_link = tk.Label(homepage_frame, text="opencolloids.com", highlightbackground=BACKGROUND_COLOR, background=BACKGROUND_COLOR, fg="blue", cursor="arrow")#"hand2")
        self.link_font = tkFont.Font(self.label_link, self.label_link.cget("font"))
        self.link_font_underline = tkFont.Font(self.label_link, self.label_link.cget("font"))
        self.link_font_underline.configure(underline = True)

        self.label_link.bind("<Button-1>", self.homepage_url_callback)
        self.label_link.grid(row=0,column=0)
        self.label_link.bind("<Enter>", self.underline_link)
        self.label_link.bind("<Leave>", self.remove_underline_link)

    def homepage_url_callback(self, event):
        webbrowser.open_new(r"http://www.opencolloids.com")

    def underline_link(self, event):
        self.label_link.config(text="opencolloids.com", font=self.link_font_underline, fg="navy")# underline = True)

    def remove_underline_link(self, event):
        self.label_link.config(text="opencolloids.com", font=self.link_font, fg="blue")# underline = False)
    

    def run(self, user_input_data):
        self.update_user_settings(user_input_data)
        self.export_parameters()

        if self.image_source.get_value() == "Local images":
            if user_input_data.auto_test_parameters == None:
                user_input_data.import_files = tkFileDialog.askopenfilenames(parent = self.root, title="Select files", initialdir=PATH_TO_SCRIPT)

                user_input_data.number_of_frames = len(user_input_data.import_files)
            else:
                if os.path.exists(user_input_data.auto_test_parameters):
                    data = []

                    writer = csv.reader(open(user_input_data.auto_test_parameters, 'r'))
                    for row in writer:
                        #print (row)
                        data.append(row)
                    impotImg = os.path.dirname(os.path.dirname(__file__)) + data[8][1]
                    tup1=(impotImg,)
                    user_input_data.import_files = tup1
                user_input_data.number_of_frames = len(user_input_data.import_files)

        # if self.create_new_dir_boole.get_value(): #create_folder_boole
        #     new_directory = os.path.join(user_input_data.directory_string, self.filename_string.get_value())
        #     os.makedirs(new_directory)
        #     user_input_data.directory_string = new_directory
        
        # if user doesnt select files - abort
        if user_input_data.number_of_frames == 0:
            sys.exit()


        self.root.destroy()


    def quit(self):
        sys.exit()

    def import_parameters(self):

        if os.path.exists(PATH_TO_FILE):
            data = []

            writer = csv.reader(open(PATH_TO_FILE, 'r'))
            for row in writer:
                data.append(row)
            self.density_inner.set_value(data[0][1])
            self.density_outer.set_value(data[1][1])
            self.needle_diameter.set_value(data[2][1])
            self.residuals_boole.set_value(data[3][1])
            self.profiles_boole.set_value(data[4][1])
            self.IFT_boole.set_value(data[5][1])

            given_image_source = data[6][1]
            if given_image_source in IMAGE_SOURCE_OPTIONS:
                self.image_source.set_value(given_image_source) # set image source
            else:
                self.directory.set_value("")
            
            self.number_frames.set_value(data[7][1])
            self.wait_time.set_value(data[8][1])
            self.save_images_boole.set_value(data[9][1]) # do this after others
            self.create_new_dir_boole.set_value(data[10][1])

            self.filename_string.set_value(data[11][1])

            
            given_dir = data[12][1]

            self.threshold_val.set_value(data[13][1])

            if os.path.isdir(given_dir):
                self.directory.set_value(given_dir) # set given directory
                # print(self.directory._directory_string.get_value())
            else:
                self.directory.set_value(os.getcwd()) # current directory of Terminal


    def update_user_settings(self, user_input_data):
        user_input_data.screen_resolution = self.screen_resolution
        user_input_data.drop_density = self.density_inner.get_value()
        user_input_data.continuous_density = self.density_outer.get_value()
        user_input_data.needle_diameter_mm= self.needle_diameter.get_value()
        user_input_data.residuals_boole = self.residuals_boole.get_value()
        user_input_data.profiles_boole = self.profiles_boole.get_value()
        user_input_data.interfacial_tension_boole = self.IFT_boole.get_value()
        user_input_data.image_source = self.image_source.get_value()
        user_input_data.number_of_frames = self.number_frames.get_value()
        user_input_data.wait_time = self.wait_time.get_value()
        user_input_data.save_images_boole = self.save_images_boole.get_value()
        user_input_data.create_folder_boole = self.create_new_dir_boole.get_value()
        temp_filename = self.filename_string.get_value()
        if temp_filename == '':
            temp_filename = "Extracted_data"
        user_input_data.filename = temp_filename + IMAGE_EXTENSION
        user_input_data.directory_string = self.directory.get_value()




    def export_parameters(self):
        parameter_vector = ([
            ('Drop density', self.density_inner.get_value()),
            ('Continuous density', self.density_outer.get_value()),
            ('Needle diameter',self.needle_diameter.get_value()),
            ('Plot residuals',self.residuals_boole.get_value()),
            ('Plot profiles',self.profiles_boole.get_value()),
            ('Plot IFT',self.IFT_boole.get_value()),
            ('Image source',self.image_source.get_value()),
            ('Number of frames',self.number_frames.get_value()),
            ('Wait time',self.wait_time.get_value()),
            ('Save images',self.save_images_boole.get_value()),
            ('Create new data folder',self.create_new_dir_boole.get_value()),
            ('Filename',self.filename_string.get_value()),
            ('Directory',self.directory.get_value()),
            ('Threshold value', self.threshold_val.get_value())
        ])
        writer = csv.writer(open(PATH_TO_FILE, 'w'))
        for row in parameter_vector:
            writer.writerow(row)



    # def validate_float(self, value_if_allowed):
    #     if text in '0123456789.-+':
    #         try:
    #             float(value_if_allowed)
    #             return True
    #         except ValueError:
    #             return False
    #     else:
    #         return False
    def validate_float(self, action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):
        # print "OnValidate:"
        # print "d='%s'" % action
        # print "i='%s'" % index
        # print "P='%s'" % value_if_allowed
        # print "s='%s'" % prior_value
        # print "S='%s'" % text
        # print "v='%s'" % validation_type
        # print "V='%s'" % trigger_type
        # print "W='%s'" % widget_name
        if value_if_allowed == '':
            return True
        elif value_if_allowed == '.':
            return True
        else:
            if text in '0123456789.-+':
                try:
                    float(value_if_allowed)
                    return True
                except ValueError:
                    return False
            else:
                return False


    def validate_int(self, action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):
        if self.initialise == True:
            return True
        elif value_if_allowed == '':
            # self.recheck_wait_state(0)
            return True
        elif value_if_allowed == '0':
            return False
        else:
            if text in '0123456789':
                try:
                    int_value = int(value_if_allowed)
                    # self.recheck_wait_state(int_value)
                    return True
                except ValueError:
                    return False
            else:
                return False


class IntegerEntryStyle():
    def __init__(self, parent, frame, text_left,  rw=0, cl=0, pdx=0, width_specify=10):
        self.label = tk.Label(frame, text=text_left, background=BACKGROUND_COLOR)
        self.label.grid(row=rw, column=cl, sticky="w")
        self.text_variable = tk.StringVar()
        vcmd_int = (parent.root.register(parent.validate_int),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.entry = tk.Entry(frame, highlightbackground=BACKGROUND_COLOR, textvariable=self.text_variable, validate = 'key', validatecommand = vcmd_int)
        self.entry.config(width=width_specify)
        self.entry.grid(row=rw, column=cl+1, sticky="we", padx=pdx)

    def get_value(self):
        return int("0" + self.text_variable.get())

    def set_value(self, value):
        self.text_variable.set(str(int(value)))

    def disable(self):
        self.entry.config(state="disabled")
        self.label.config(state="disabled")

    def normal(self):
        self.entry.config(state="normal")
        self.label.config(state="normal")

class FloatEntryStyle():
    def __init__(self, parent, frame, text_left, rw=0, label_width=None, width_specify=10):
        self.label = tk.Label(frame, text=text_left, background=BACKGROUND_COLOR, width=label_width)
        self.label.grid(row=rw, column=0, sticky="w")
        self.text_variable = tk.StringVar()
        vcmd_float = (parent.root.register(parent.validate_float),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.entry = tk.Entry(frame, highlightbackground=BACKGROUND_COLOR, textvariable=self.text_variable, validate = 'key', validatecommand = vcmd_float)
        self.entry.config(width=width_specify)
        self.entry.grid(row=rw, column=1, sticky="we")

    def get_value(self):
        return float("0" + self.text_variable.get())

    def set_value(self, value):
        self.text_variable.set(str(float(value)))

    def disable(self):
        self.entry.config(state="disabled")
        self.label.config(state="disabled")

    def normal(self):
        self.entry.config(state="normal")
        self.label.config(state="normal")

class TextEntryStyle():
    def __init__(self, parent, frame, text_left, rw=0, width_specify=10, stckyL="w", stckyE="w"):
        self.label = tk.Label(frame, text=text_left, background=BACKGROUND_COLOR)
        self.label.grid(row=rw, column=0, sticky=stckyL)
        self.text_variable = tk.StringVar()
        self.entry = tk.Entry(frame, highlightbackground=BACKGROUND_COLOR, textvariable=self.text_variable)
        self.entry.config(width=width_specify)
        self.entry.grid(row=rw, column=1, sticky=stckyE)        

    def get_value(self):
        # if self.text_variable.get() == '':
        #     self.set_value(self.default_string)
        return self.text_variable.get()

    def set_value(self, value):
        self.text_variable.set(value)

    def disable(self):
        self.entry.config(state="disabled")
        self.label.config(state="disabled")

    def normal(self):
        self.entry.config(state="normal")
        self.label.config(state="normal")


class DirectoryEntryStyle():
    def __init__(self, parent, frame, text_left, rw=0, entry_width=20):
        self.label = tk.Label(frame, text=text_left, background=BACKGROUND_COLOR)
        self.label.grid(row=rw, column=0, sticky="w")
        self.directory_string = tk.StringVar()
        self._directory_string = tk.StringVar()
        # self.directory_string.set('~/')
        # self.directory_string.set(os.path.dirname(os.path.realpath(__file__))) # directory of file
        # self.directory_string.set(os.getcwd()) # current directory of Terminal
        # self._directory_string.set(self.clip_dir(self.directory_string.get()))
        self.entry = tk.Entry(frame, highlightbackground=BACKGROUND_COLOR, textvariable=self._directory_string, state="readonly")
        # self.entry.config(width=entry_width)
        self.entry.config(width=49)
        self.entry.grid(row=rw, column=1, columnspan=2, sticky="ew")
        self.button = tk.Button(frame, text="Browse", command=lambda:self.update_directory(parent), highlightbackground=BACKGROUND_COLOR)
        self.button.grid(row=rw, column=3, sticky="e")

    def get_value(self):
        return self.directory_string.get()

    def set_value(self, value):
        self.directory_string.set(value)
        self._directory_string.set(self.clip_dir(self.directory_string.get()))

    def disable(self):
        self.label.config(state="disabled")
        self.entry.config(state="disabled")
        self.button.config(state="disabled")

    def normal(self):
        self.label.config(state="normal")
        self.entry.config(state="normal")
        self.button.config(state="normal")

    def update_directory(self, master):
        initdir = self.directory_string.get()
        temp_dir = tkFileDialog.askdirectory(parent = master, title="Select output data location", initialdir=initdir)
        if temp_dir is not "":
            self.directory_string.set(temp_dir)
            self._directory_string.set(self.clip_dir(temp_dir))

    # clips the directory to MAX_DIR_LEN characters
    def clip_dir(self, string):
        MAX_DIR_LEN=50
        if len(string) > MAX_DIR_LEN:
            return "..." + string[-(MAX_DIR_LEN+3):]
        else:
            return string

    def grid_forget(self):
        self.label.grid_forget()
        self.entry.grid_forget()
        self.button.grid_forget()

    # # this does not clip the directory...
    # def clip_dir(self, string):
    #     return string




class FloatComboboxStyle():
    def __init__(self, parent, frame, text_left, options_list, rw=0, width_specify=10, label_width=None):
        self.label = tk.Label(frame, text=text_left, background=BACKGROUND_COLOR, width=label_width)
        self.label.grid(row=rw, column=0, sticky="w")
        self.text_variable = tk.StringVar()
        vcmd_float = (parent.root.register(parent.validate_float),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.combobox = ttk.Combobox(frame, textvariable=self.text_variable, validate = 'key', validatecommand = vcmd_float)
        self.combobox['values'] = options_list
        self.combobox.config(width=width_specify)
        self.combobox.grid(row=rw, column=1, sticky="we")

    def get_value(self):
        return float("0" + self.text_variable.get())

    def set_value(self, value):
        self.text_variable.set(str(float(value)))

    def disable(self):
        self.combobox.config(state="disabled")
        self.label.config(state="disabled")

    def normal(self):
        self.combobox.config(state="normal")
        self.label.config(state="normal")



class CheckButtonStyle():
    def __init__(self, parent, frame, text_left, rw=0, cl=0, width_specify=10, pdx=0, pdy=2, stcky="w"): #, pd=5
        self._save_previous_variable = 0
        self.int_variable = tk.IntVar()
        self.check_button = tk.Checkbutton(frame, text=text_left, background=BACKGROUND_COLOR, variable=self.int_variable)        
        self.check_button.grid(row=rw, column=cl, sticky=stcky, pady=pdy, padx=pdx)#"CENTER") # sticky="w" padx=pd, 

    def get_value(self):
        return self.int_variable.get()

    def set_value(self, value):
        self.int_variable.set(value)

    def disable(self):
        self._save_previous_variable = self.get_value()
        self.set_value(0)
        self.check_button.config(state="disabled")

    def normal(self):
        self.set_value(self._save_previous_variable)
        self.check_button.config(state="normal")

    def state(self):
        return self.check_button.config()['state'][-1]

    def grid_forget(self):
        self.check_button.grid_forget()


class OptionMenuStyle():
    def __init__(self, parent, frame, text_left, options_list, rw=0, width_specify=15, label_width=None):
        self.entry_list = options_list
        self.label = tk.Label(frame, text=text_left, background=BACKGROUND_COLOR, width=label_width, anchor="w")
        self.label.grid(row=rw, column=0, sticky="w")
        self.text_variable = tk.StringVar()
        self.optionmenu = apply(tk.OptionMenu, (frame, self.text_variable) + tuple(self.entry_list))
        self.optionmenu.config(bg = BACKGROUND_COLOR, width=width_specify)
        self.optionmenu.grid(row=rw, column=1, sticky="w")

    def get_value(self):
        return self.text_variable.get()

    def set_value(self, value):
        if value in self.entry_list:
            self.text_variable.set(value)
        else:
            self.text_variable.set(entry_list[0])

    def disable(self):
        self.optionmenu.config(state="disabled")
        self.label.config(state="disabled")

    def normal(self):
        self.optionmenu.config(state="normal")
        self.label.config(state="normal")


class LabelFrameStyle():
    def __init__(self, parent, text_left, rw=0, cl=0, clspan=2, rwspan=1, stcky="w", pdx=15, pdy=10):
        self = tk.LabelFrame(parent, text=text_left, padx=30, pady=10)
        self.config(background=BACKGROUND_COLOR)
        # self.grid(row=rw, column=cl, columnspan=clspan, rowspan=rwspan, sticky=stcky, padx=pdx, pady=pdy)
        self.grid(row=rw, columnspan=clspan, rowspan=rwspan, sticky="w", padx=pdx, pady=pdy)



if __name__ == '__main__':
    UserInterface()
    # ui.app()









