#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function
import numpy as np
from jacobian import rowJacobian
from abc import abstractmethod

np.set_printoptions(suppress=True)
np.set_printoptions(precision=3)

dot = np.dot

# implements the Levenberg--Marquardt--Fletcher algorithm to find parameters
# Levenberg--Marquardt--Fletcher Automated Optimisation


class BasicFitData(object):

    @abstractmethod
    def fit_experimental_drop(self, experimental_drop, drop_data, user_inputs, tolerances): pass

    # ensure nu is between 2 and 10
    def bounded_2_to_10(self, nu):
        if nu < 2:
            nu = 2  # rescale nu if too small
        elif nu > 10:
            nu = 10 # rescale nu if too large
        return nu

    def inverse_matrix(self, matrix):
        # check if matrix is singular via
        # condition_number = np.linalg.cond(matrix)
        return np.linalg.inv(matrix)


    def calculate_A_v_S(self, experimental_drop, drop_data, tolerances):
        lenpoints = len(experimental_drop.drop_data)
        m_parameters = len(drop_data.params)
        A = np.empty((m_parameters, m_parameters))
        A.fill(0.0)
        v = np.empty((m_parameters, 1))
        v.fill(0.0)
        S = 0.0
        residual_vector = np.zeros(lenpoints)
        arc_lengths_vector = np.zeros(lenpoints)
        # residual_vector.fill(0)
        for i in range(0, lenpoints):
            x, y  = experimental_drop.drop_data[i]
            JACrowi, residual_vector[i] = rowJacobian(x, y, drop_data, tolerances) # calculate the Jacobian and resiual for each point
            # arc_lengths_vector[i] = drop_data.s_0
            arc_lengths_vector[i] = drop_data.s_previous
            S += residual_vector[i]**2
            for j in range(0, m_parameters):
                v[j] += JACrowi[j]*residual_vector[i]
                for k in range(0, j+1):
                    A[j][k] += JACrowi[j]*JACrowi[k]
        for j in range(0, m_parameters):
            for k in range(j, m_parameters):
                A[j][k] = A[k][j]
        drop_data.residuals = residual_vector
        drop_data.arc_lengths = arc_lengths_vector
        return [A, v, S]

    # test whether routine has converged
    def to_continue(self, scaled_delta, v, objective_function, steps_LMF, tolerances):
        flag1 = self.convergence_in_parameters(scaled_delta, tolerances)
        flag2 = self.convergence_in_gradient(v, tolerances)
        flag3 = self.convergence_in_objective(objective_function, tolerances)
        flag4 = self.maximum_steps_exceeded(steps_LMF, tolerances)
        return not ( flag1 | flag2 | flag3 | flag4 )

    # test for convergence in parameters
    def convergence_in_parameters(self, scaled_delta, tolerances):
        max_delta = max([abs(scaled_delta[i]) for i in range(0, len(scaled_delta))])
        if max_delta < tolerances.DELTA_TOL:
            print("Convergence in parameters")
            return True
        else:
            return False

    # test for convergence in gradient
    def convergence_in_gradient(self, v, tolerances):
        max_gradient = max([abs(v[i]) for i in range(0, len(v))])
        if max_gradient < tolerances.GRADIENT_TOL:
            print("Convergence in gradient")
            return True
        else:
            return False

    # test for convergence in objective function
    def convergence_in_objective(self, objective_function, tolerances):
        if objective_function < tolerances.OBJECTIVE_TOL:
            print("Convergence in objective")
            return True
        else:
            return False

    # test maximum steps
    def maximum_steps_exceeded(self,steps_LMF, tolerances):
        if steps_LMF > tolerances.MAXIMUM_FITTING_STEPS:
            print("Maximum steps exceeded")
            return True
        else:
            return False

    # initialise terminal output to the terminal

    def intialise_print_output(self):

        print("__________________________________________________________________________")
        print("| Step |  Error   | x-centre | z-centre | Apex R_0 |   Bond   | w degree |")

    # print current output to the terminal

    @abstractmethod
    def print_current_parameters(self, steps_LMF, objective_function, drop_params, y_offset): pass



