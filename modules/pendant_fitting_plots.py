import basic_fitting_plots
import numpy as np

cos = np.cos
sin = np.sin
dot = np.dot


class PendantFittingPlots(basic_fitting_plots.BasicFittingPlots):

    # def generate_profile(fitted_drop):
    def update_profile_plot(self, experimental_drop, fitted_drop, user_inputs):
        if self.profile_initialised == False:
            self.setup_profile_plot(experimental_drop, fitted_drop)
            self.profile_initialised = True
        # x_apex, y_apex, radius_apex, bond_number, omega_rotation = fitted_drop.params
        x_apex, y_apex, radius_apex, bond_number, omega_rotation = fitted_drop.previous_params
        rotation_matrix = [[cos(omega_rotation), -sin(omega_rotation)], [sin(omega_rotation), cos(omega_rotation)]]
        reflect_rotation_matrix = dot([[-1, 0], [0, 1]], rotation_matrix)
        # DEsoln = odeint(deriv, x_initial, s_plot)
        # s_needle = fitted_drop.previous_guess
        # s_needle = fitted_drop.s_0
        s_needle = max(abs(fitted_drop.arc_lengths))
        profile = self.theoretical_profile(s_needle, fitted_drop)
        # DEL = dot(dot(profile, [[-1, 0], [0, 1]] ), rotationMatrix)
        profile_left = dot(profile, reflect_rotation_matrix)
        profile_right = dot(profile, rotation_matrix)
        drop_x_left = x_apex + radius_apex * profile_left[:, 0]
        drop_y_left = y_apex + radius_apex * profile_left[:, 1]
        drop_x_right = x_apex + radius_apex * profile_right[:, 0]
        drop_y_right = y_apex + radius_apex * profile_right[:, 1]

        self.profile_line_left.set_xdata(drop_x_left)
        self.profile_line_left.set_ydata(drop_y_left)
        self.profile_line_right.set_xdata(drop_x_right)
        self.profile_line_right.set_ydata(drop_y_right)

        self.fig_profile.canvas.draw()

