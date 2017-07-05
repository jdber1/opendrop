import basic_fit_data
import numpy as np
import os
from sessile_fitting_plots import SessileFittingPlots

dot = np.dot


class SessileFitData(basic_fit_data.BasicFitData):

    def fit_experimental_drop(self, experimental_drop, drop_data, user_inputs, tolerances):
        fitting_plots = SessileFittingPlots()
        degrees_of_freedom = len(experimental_drop.drop_data) - drop_data.parameter_dimensions + 1
        RHO = 0.25
        SIGMA = 0.75
        lmbda = 0  # initialise value of lambda
        steps_LMF = 0  # number of steps taken
        self.intialise_print_output()
        # drop_data.s_0 = 0.05 * drop_data.max_s
        # drop_data.s_left = 0.05 * drop_data.max_s   JB edit 26/3/15
        # drop_data.s_right = 0.05 * drop_data.max_s JB edit 26/3/15
        loop = True
        if user_inputs.auto_test_parameters != None:
            f = open(os.path.dirname(os.path.dirname(__file__)) + '/standard_outputs/sessileDrop.txt', "r")
            flag = 1
        while (loop):
            drop_data.s_left = 0.05 * drop_data.max_s  # JB edit 26/3/15
            drop_data.s_right = 0.05 * drop_data.max_s  # JB edit 26/3/15

            drop_data.previous_params = drop_data.params
            A, v, Snew = self.calculate_A_v_S(experimental_drop, drop_data, tolerances)
            if lmbda != 0:
                A_plus_lambdaI = A + lmbda * np.diag(np.diag(A))
            else:
                A_plus_lambdaI = A
            inv = self.inverse_matrix(A_plus_lambdaI)
            delta = -dot(inv, v).T
            if steps_LMF == 0:  # initialisation step
                drop_data.params = drop_data.params + (delta)[0]
                Sold = Snew  # initialisation step
            else:
                R = (Sold - Snew) / (dot(delta, (-2 * v - dot(A.T, delta.T))))
                if R < RHO:
                    nu = self.bounded_2_to_10(2 - (Snew - Sold) / (dot(delta, v)))
                    if lmbda == 0:
                        lmbdaC = 1 / max([abs(inv[i][i]) for i in range(0, len(inv))])
                        lmbda = lmbdaC  # calculate lambda_c and set lambda
                        nu = nu / 2
                    lmbda = nu * lmbda  # rescale lambda
                if R > SIGMA:
                    if lmbda != 0:
                        lmbda = lmbda / 2
                        if lmbda < lmbdaC:
                            lmbda = 0
                deltaS = Snew - Sold  # calculate reduction in objective function
                if deltaS < 0:
                    drop_data.params = drop_data.params + (delta)[0]  # if objective reduces accept
                    Sold = Snew
            objective_function = Snew / degrees_of_freedom
            steps_LMF += 1

            y_offset = (experimental_drop.image.shape[0] - user_inputs.drop_region[1][1]) + (
            experimental_drop.image.shape[0] - user_inputs.drop_region[0][1])
            self.print_current_parameters(steps_LMF, objective_function, drop_data.params, y_offset)

            if user_inputs.auto_test_parameters != None:
                readline = f.readline()

                result = self.check_outputs(steps_LMF, objective_function, drop_data.params, y_offset, readline)
                if result == 0:
                    flag = 0

            fitting_plots.update_plots(experimental_drop, drop_data, user_inputs)

            loop = self.to_continue(delta[0] / drop_data.params, v, objective_function, steps_LMF, tolerances)

        if user_inputs.auto_test_parameters != None:
            if flag == 1:
                print("current parameters are correct")
            if flag == 0:
                print("current parameters are incorrect")

        if user_inputs.auto_test_parameters != None:

            fitting_plots.fig_residual.savefig(os.path.dirname(os.path.dirname(__file__)) + '/outputs/sessileDrop_residual.jpg')
            fitting_plots.fig_profile.savefig(os.path.dirname(os.path.dirname(__file__)) + '/outputs/sessileDrop_drop_profile.jpg')

            img1 = open(os.path.dirname(os.path.dirname(__file__)) + '/standard_outputs/sessileDrop_residual.jpg', "r")
            img2 = open(os.path.dirname(os.path.dirname(__file__)) + '/outputs/sessileDrop_residual.jpg', "r")

            if img1.read() == img2.read():
                print("the residual output is correct")
            else:
                print("the residual output is incorrect")

            img1 = open(os.path.dirname(os.path.dirname(__file__)) + '/standard_outputs/sessileDrop_drop_profile.jpg', "r")
            img2 = open(os.path.dirname(os.path.dirname(__file__)) + '/outputs/sessileDrop_drop_profile.jpg', "r")

            if img1.read() == img2.read():
                print("the drop_profile output is correct")
            else:
                print("the drop_profile output is incorrect")
        drop_data.fitted = True

    def print_current_parameters(slef, steps_LMF, objective_function, drop_params, y_offset):
        x_apex, y_apex, radius_apex, bond_number, omega_rotation = drop_params

        y_apex = -y_apex + y_offset

        print(
            "| %3d  | %8.4f | %8.4f | %8.4f | %8.4f | %8.5f | %8.5f |" %
            (steps_LMF, objective_function, x_apex, y_apex, radius_apex, bond_number, 180 * omega_rotation / np.pi)
        )


    def check_outputs(self, steps_LMF, objective_function, drop_params, y_offset, readline):
        x_apex, y_apex, radius_apex, bond_number, omega_rotation = drop_params
        y_apex = -y_apex + y_offset
        string = (
            "| %3d  | %8.4f | %8.4f | %8.4f | %8.4f | %8.5f | %8.5f |\n" %
            (steps_LMF, objective_function, x_apex, y_apex, radius_apex, bond_number, 180 * omega_rotation / np.pi)
        )
        if readline == string:
            return 1
        else:
            return 0



