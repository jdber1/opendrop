#!/usr/bin/env python
#coding=utf-8

import math
import matplotlib.pyplot as plt
import numpy as np
from abc import abstractmethod
cos = np.cos
sin = np.sin
dot = np.dot


class BasicFittingPlots(object):
    def __init__(self):
        plt.ion()
        self.residual_initialised = False
        self.profile_initialised = False

    # def setup_plots(self, experimental_drop, residual_plot_boole=False, profile_plot_boole=False):
    #     plt.ion()
    #     if residual_plot_boole:
    #         self.setup_residual_plot(experimental_drop)
    #     if profile_plot_boole:
    #         self.setup_profile_plot(experimental_drop)

    def update_plots(self, experimental_drop, fitted_drop, user_inputs):
        if user_inputs.profiles_boole:
            self.update_profile_plot(experimental_drop, fitted_drop, user_inputs)
        if user_inputs.residuals_boole:
            self.update_residual_plot(experimental_drop, fitted_drop)

    def setup_profile_plot(self, experimental_drop, fitted_drop):
        self.fig_profile = plt.figure("Drop profile")
        plt.clf()
        self.subfig_profile = self.fig_profile.add_subplot(1,1,1)
        height, width = experimental_drop.image.shape[:2]
        plt.imshow(np.flipud(experimental_drop.image), origin='lower', cmap = 'gray')
        plt.axis([0, width, 0, height], aspect=1)
        # x_data, y_data = generate_profile()
        spoints = fitted_drop.s_points
        self.profile_line_left, = self.subfig_profile.plot(np.zeros(spoints+1), np.zeros(spoints+1), "--r", linewidth = 2.0)
        self.profile_line_right, = self.subfig_profile.plot(np.zeros(spoints+1), np.zeros(spoints+1), "--r", linewidth = 2.0)


        # self.subfig_profile.plot(x_data, y_data, '--r', linewidth = 2.0)

    # def update_profile_plot(self, fitted_drop):
    #     self.profile_line.set_xdata(fitted_drop.arc_lengths)
    #     self.profile_line.set_ydata(fitted_drop.residuals)
    #     self.fig_profile.canvas.draw()

    def setup_residual_plot(self, n_points): # fitted_drop):
        self.fig_residual = plt.figure("Residuals")
        plt.clf()
        self.subfig_profile = self.fig_residual.add_subplot(1,1,1)
        self.residual_data, = self.subfig_profile.plot(np.zeros(n_points), np.zeros(n_points), "bo")
        # # self.residual_data, = self.subfig_profile.plot(fitted_drop.arc_lengths, fitted_drop.residuals, "bo")
        # self.residual_data, = self.subfig_profile.plot(fitted_drop.residuals, fitted_drop.residuals, "bo")
        # self.residual_data, = self.subfig_profile.scatter(fitted_drop.arc_lengths, fitted_drop.residuals, s=80, facecolors='none', edgecolors='b')
        # # self.residual_data, = self.subfig_profile.scatter(fitted_drop.residuals, fitted_drop.residuals, s=80, facecolors='none', edgecolors='b')

    def update_residual_plot(self, experimental_drop, fitted_drop):
        n_points = len(fitted_drop.residuals)

        if self.residual_initialised == False:
            self.setup_residual_plot(n_points) #fitted_drop)
            self.residual_initialised = True
        # self.residual_data.set_xdata(fitted_drop.arc_lengths)
        # self.residual_data.set_xdata(fitted_drop.residuals)
        # self.residual_data.set_ydata(fitted_drop.residuals)
        
        
        x_apex = fitted_drop.params[0]
        # self.residual_data.set_xdata([math.copysign(fitted_drop.arc_lengths[i], experimental_drop.drop_data[i,0] - x_apex) for i in range(n_points)])
        # self.residual_data.set_ydata([math.copysign(fitted_drop.residuals[i], 1) for i in range(n_points)]) # inside_outside(i)
        x_data = [math.copysign(fitted_drop.arc_lengths[i], experimental_drop.drop_data[i,0] - x_apex) for i in range(n_points)]
        # fitted_drop.signed_arc_lengths
        self.residual_data.set_xdata(x_data)
        self.residual_data.set_ydata(fitted_drop.residuals)
        self.residual_data.axes.relim()
        self.residual_data.axes.autoscale_view(True,True,True)
        self.fig_residual.canvas.draw()
        


    # def inside_outside(self, experimental_drop, fitted_drop, i):
    #     arc_length_s = fitted_drop.arc_lengths[i]
    #     arc_length_s
    #     x_apex, y_apex, radius_apex, bond_number, omega_rotation = fitted_drop.params
    #     x_s, y_s, phi_s = fitted_drop.profile(arc_length_s)[:3]
    #     x_drop, y_drop = experimental_drop.drop_data[i]


    # def generate_residuals(self, fitted_drop):
    #     n_points = len(fitted_drop.residuals)
    #     drop_data.arc_lengths
    #     self.residuals_plot_y = [math.copysign(fitted_drop.residuals[i], inside_outside(i)) for i in range(n_points)]
    #     self.residuals_plot_x = [math.copysign(arc_length_matrix[i], xydata[i,0] - X0) for i in range(n_points)]


    def theoretical_profile(self, s_needle, fitted_drop):
        Delta_s = fitted_drop.max_s / fitted_drop.s_points
        n_floor = int(s_needle / Delta_s)
        data = np.array(fitted_drop.theoretical_data)[:,:2]
        final_data_point = fitted_drop.profile(s_needle)[:2]
        data[n_floor+1:] = final_data_point # trim the final data point
        return data

    # def theoretical_profile(s_needle, fitted_drop):
    #     Delta_s = fitted_drop.max_s / fitted_drop.s_points
    #     n_floor = int(s_needle / Delta_s)
    #     data = np.array(fitted_drop.theoretical_data[:n_floor+2])
    #     data[-1] = fitted_drop.profile(s_needle) # trim the final data point
    #     return data[:,:2]
    @abstractmethod
    def update_profile_plot(self, experimental_drop, fitted_drop, user_inputs): pass




