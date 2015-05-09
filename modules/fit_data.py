#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function
import numpy as np
from jacobian import rowJacobian
from FittingPlots import FittingPlots

np.set_printoptions(suppress=True)
np.set_printoptions(precision=3)

dot = np.dot

# implements the Levenberg--Marquardt--Fletcher algorithm to find parameters
# Levenberg--Marquardt--Fletcher Automated Optimisation
def fit_experimental_drop(experimental_drop, drop_data, user_inputs, tolerances):
    fitting_plots = FittingPlots()
    degrees_of_freedom = len(experimental_drop.drop_data) - drop_data.parameter_dimensions + 1
    RHO = 0.25
    SIGMA = 0.75
    lmbda = 0 # initialise value of lambda
    steps_LMF = 0 # number of steps taken
    intialise_print_output()
    # drop_data.s_0 = 0.05 * drop_data.max_s
    #drop_data.s_left = 0.05 * drop_data.max_s   JB edit 26/3/15
    #drop_data.s_right = 0.05 * drop_data.max_s JB edit 26/3/15
    loop = True
    while(loop):
        drop_data.s_left = 0.05 * drop_data.max_s #JB edit 26/3/15
        drop_data.s_right = 0.05 * drop_data.max_s #JB edit 26/3/15

        drop_data.previous_params = drop_data.params
        A, v, Snew = calculate_A_v_S(experimental_drop, drop_data, tolerances)
        if lmbda != 0:
            A_plus_lambdaI = A + lmbda * np.diag(np.diag(A))
        else:
            A_plus_lambdaI = A
        inv = inverse_matrix(A_plus_lambdaI)
        delta = -dot(inv, v).T
        if steps_LMF == 0: # initialisation step
            drop_data.params = drop_data.params + (delta)[0]
            Sold = Snew # initialisation step
        else:
            R = (Sold - Snew) / (dot(delta, (-2 * v - dot(A.T, delta.T))))
            if R < RHO:
                nu = bounded_2_to_10( 2 - (Snew - Sold)/(dot(delta, v)) )
                if lmbda == 0:
                    lmbdaC = 1/max([abs(inv[i][i]) for i in range(0, len(inv))])
                    lmbda = lmbdaC # calculate lambda_c and set lambda
                    nu = nu / 2
                lmbda = nu * lmbda # rescale lambda
            if R > SIGMA:
                if lmbda != 0:
                    lmbda = lmbda / 2
                    if lmbda < lmbdaC:
                        lmbda = 0
            deltaS = Snew - Sold # calculate reduction in objective function
            if deltaS < 0:
                drop_data.params = drop_data.params + (delta)[0] # if objective reduces accept
                Sold = Snew
        objective_function = Snew / degrees_of_freedom
        steps_LMF += 1
        print_current_parameters(steps_LMF, objective_function, drop_data.params)

        fitting_plots.update_plots(experimental_drop, drop_data, user_inputs)

        loop = to_continue(delta[0] / drop_data.params, v, objective_function, steps_LMF, tolerances)
    drop_data.fitted = True

# ensure nu is between 2 and 10
def bounded_2_to_10(nu):
    if nu < 2:
        nu = 2  # rescale nu if too small
    elif nu > 10:
        nu = 10 # rescale nu if too large
    return nu

def inverse_matrix(matrix):
    # check if matrix is singular via 
    # condition_number = np.linalg.cond(matrix)
    return np.linalg.inv(matrix)


def calculate_A_v_S(experimental_drop, drop_data, tolerances):
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
def to_continue(scaled_delta, v, objective_function, steps_LMF, tolerances):
    flag1 = convergence_in_parameters(scaled_delta, tolerances)
    flag2 = convergence_in_gradient(v, tolerances)
    flag3 = convergence_in_objective(objective_function, tolerances)
    flag4 = maximum_steps_exceeded(steps_LMF, tolerances)
    return not ( flag1 | flag2 | flag3 | flag4 )

# test for convergence in parameters
def convergence_in_parameters(scaled_delta, tolerances):
    max_delta = max([abs(scaled_delta[i]) for i in range(0, len(scaled_delta))])
    if max_delta < tolerances.DELTA_TOL:
        print("Convergence in parameters")
        return True
    else:
        return False

# test for convergence in gradient
def convergence_in_gradient(v, tolerances):
    max_gradient = max([abs(v[i]) for i in range(0, len(v))])
    if max_gradient < tolerances.GRADIENT_TOL:
        print("Convergence in gradient")
        return True
    else:
        return False

# test for convergence in objective function
def convergence_in_objective(objective_function, tolerances):
    if objective_function < tolerances.OBJECTIVE_TOL:
        print("Convergence in objective")
        return True
    else:
        return False

# test maximum steps
def maximum_steps_exceeded(steps_LMF, tolerances):
    if steps_LMF > tolerances.MAXIMUM_FITTING_STEPS:
        print("Maximum steps exceeded")
        return True
    else:
        return False

# initialise terminal output to the terminal
def intialise_print_output():
    print("__________________________________________________________________________")
    print("| Step |  Error   | x-centre | z-centre | Apex R_0 |   Bond   | w degree |")

# print current output to the terminal
def print_current_parameters(steps_LMF, objective_function, drop_params):
    x_apex, y_apex, radius_apex, bond_number, omega_rotation = drop_params
    print(
          "| %3d  | %8.4f | %8.4f | %8.4f | %8.4f | %8.5f | %8.5f |" % 
          (steps_LMF, objective_function, x_apex, y_apex, radius_apex, bond_number, 180*omega_rotation/np.pi) 
        )

