#!/usr/bin/env python
# coding=utf-8

import matplotlib.pyplot as plt
import numpy as np

# IFT_MAX = 100.
# VOL_MAX = 10.
# AREA_MAX = 10.
PAD = 0.1

class PlotManager(object):
    def __init__(self, wait_time, n_frames):
        self.max_time = wait_time * n_frames
        self.time_values = np.zeros(n_frames)
        self.IFT_values = np.zeros(n_frames)
        self.volume_values = np.zeros(n_frames)
        self.area_values = np.zeros(n_frames)
        self.plots_initialised = False
        self.axes_update = None
        self.IFT_axis_max = 0
        self.volume_axis_max = 0
        self.area_axis_max = 0

    def append_data_time(self, data_value, position):
        self.time_values[position:] = data_value
        # self.check_max_time(data_value)

    def append_data_IFT(self, data_value, position):
        self.IFT_values[position:] = data_value

    def append_data_volume(self, data_value, position):
        self.volume_values[position:] = data_value

    def append_data_area(self, data_value, position):
        self.area_values[position:] = data_value

    def append_data(self, data_vector, position):
        self.append_data_time(data_vector[0], position)
        self.append_data_IFT(data_vector[1], position)
        self.append_data_volume(data_vector[2], position)
        self.append_data_area(data_vector[3], position)

    def append_data_plot(self, data_vector, position):
        self.append_data(data_vector, position)
        self.check_plot_axes(data_vector)
        self.update_plot()



    def initialise_plot(self):
        plt.ion()
        self.fig = plt.figure("figures")
        self.IFT_plot = self.fig.add_subplot(311)
        self.IFT_line, = self.IFT_plot.plot(self.time_values, self.IFT_values, 'o-b')
        # self.IFT_plot.axis((0,self.max_time,0,IFT_MAX))
        self.IFT_plot.set_xlabel("Time / s")
        self.IFT_plot.set_ylabel("Interfacial tension / (mN / m)")

        self.volume_plot = self.fig.add_subplot(312)
        # self.volume_plot.axis((0,self.max_time,0,VOL_MAX))
        self.volume_line, = self.volume_plot.plot(self.time_values, self.volume_values, 'o-r')
        self.volume_plot.set_xlabel("Time / s")
        self.volume_plot.set_ylabel("Volume / uL")
        # self.volume_plot.set_ylabel("Volume / m^3")

        self.area_plot = self.fig.add_subplot(313)
        # self.area_plot.axis((0,self.max_time,0,AREA_MAX))
        self.area_line, = self.area_plot.plot(self.time_values, self.area_values, 'o-g')
        self.area_plot.set_xlabel("Time / s")
        # self.area_plot.set_ylabel("Area / m^2")
        self.area_plot.set_ylabel("Area / mm^2")

        # self.fig.tight_layout()


    def update_plot(self):
        if self.plots_initialised == False:
            self.initialise_plot()
            self.plots_initialised = True
        self.IFT_line.set_xdata(self.time_values)
        self.IFT_line.set_ydata(self.IFT_values)
        self.volume_line.set_xdata(self.time_values)
        self.volume_line.set_ydata(self.volume_values)
        self.area_line.set_xdata(self.time_values)
        self.area_line.set_ydata(self.area_values)
        if self.axes_update:
            self.update_plot_axes()
        self.fig.canvas.draw()

    def check_time_axis(self, new_time):
        if new_time > self.max_time:
            self.max_time = (1 + PAD) * new_time
            # self.IFT_plot.axis((0,self.max_time,0,self.IFT_axis_max))
            # self.volume_plot.axis((0,self.max_time,0,self.volume_axis_max))
            # self.area_plot.axis((0,self.max_time,0,self.area_axis_max))
            return True
        else:
            return False

    def check_IFT_axis(self, IFT_value):
        if IFT_value > ((1 - PAD) * self.IFT_axis_max):
            self.IFT_axis_max = ((1 + PAD) * IFT_value)
            return True
        else:
            return False

    def check_volume_axis(self, volume_value):
        if volume_value > ((1 - PAD) * self.volume_axis_max):
            self.volume_axis_max = ((1 + PAD) * volume_value)
            return True
        else:
            return False

    def check_area_axis(self, area_value):
        if area_value > ((1 - PAD) * self.area_axis_max):
            self.area_axis_max = ((1 + PAD) * area_value)
            return True
        else:
            return False

    def check_plot_axes(self, data_vector):
#        bool_time = self.check_time_axis(data_vector[0])
#        bool_IFT = self.check_IFT_axis(data_vector[1])
#        bool_volume = self.check_volume_axis(data_vector[2])
#        bool_area = self.check_area_axis(data_vector[3])
#        if bool_time or bool_IFT or bool_volume or bool_area:
#            # self.update_plot_axes(data_vector)
        self.axes_update = True




    def update_plot_axes(self):
        # self.IFT_plot.axis((0,self.max_time,0,self.IFT_axis_max))
        # self.volume_plot.axis((0,self.max_time,0,self.volume_axis_max))
        # self.area_plot.axis((0,self.max_time,0,self.area_axis_max))
	IFTmin,IFTmax =0.98 * min(self.IFT_values), 1.02 * max(self.IFT_values)
	volmin,volmax =0.98 * min(self.volume_values), 1.02 * max(self.volume_values)
	surmin,surmax =0.98 * min(self.area_values), 1.02 * max(self.area_values)
        self.IFT_plot.axes.set_xlim([0,self.max_time])
	self.IFT_plot.axes.set_ylim([IFTmin,IFTmax])
	self.volume_plot.axes.set_xlim([0,self.max_time])
	self.volume_plot.axes.set_ylim([volmin,volmax])
	self.area_plot.axes.set_xlim([0,self.max_time])
	self.area_plot.axes.set_ylim([surmin,surmax])	
        self.axes_update = False

    # def plot_profiles(self):
    #     # if self.plots_initialised == False:
    #         # ValueError("Plots have not yet been initialised")
    #     self.residuals_boole = True
    #     self.profiles_boole = True
    #     self.interfacial_tension_boole = True


    def close_windows(self):
        pass
