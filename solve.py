# -*- coding: utf-8 -*-
"""
Created on Fri Apr  8 01:23:57 2016

@author: trish
"""

import os.path

import sedumi_writer as sw
import solve_locally as ls
import result as res

def check_output_target(mode, output_target):
    '''
    checks if the value of output_target is appropriate:
        - output_target can't be None if mode is matlab or octave
        - at least for now, output_target can't be a file that already exists
    '''
    assert mode in ['matlab', 'octave', 'neos'], \
        "Please choose mode equal to either 'matlab', 'octave', or 'neos'."
    assert mode not in ['matlab', 'octave'] or output_target, \
        "If mode is 'matlab' or 'octave', an output_target must be provided."
    if output_target:
        assert not os.path.exists(output_target), \
            "Something already exists at output_target, we won't overwrite it."

def sdpt3_solve_problem(problem, mode, matfile_target, output_target=None, discard_matfile=True):
    '''
    A wrapper function that takes a cvxpy problem, makes the .mat file, solves
    it by NEOS or a local Matlab/SDPT3 installation, then constructs the result,
    prints it, and returns it.
    '''
    assert not os.path.exists(matfile_target), \
        "Something already exists at matfile_target, we won't overwrite it."
    check_output_target(mode, output_target)

    # Write the problem to a .mat file in Sedumi format
    problem_data = problem.get_problem_data('CVXOPT')
    sw.write_cvxpy_to_mat(problem_data, matfile_target)

    return sdpt3_solve_mat(matfile_target,
                           mode,
                           output_target=output_target,
                           discard_matfile=discard_matfile)


def sdpt3_solve_mat(matfile_path, mode, output_target=None, discard_matfile=True):
    '''
    A wrapper function that takes the path of a .mat file, solves the Sedumi
    problem it contains with NEOS or a local Matlab/SDPT3 installation, then
    constructs the result, prints it, and returns it.
    '''
    check_output_target(mode, output_target)

    # Depending on the mode, solve the problem using a local Matlab+SDPT3
    # installation or on the NEOS server
    if mode == 'matlab':
        msg = ls.matlab_solve(matfile_path,
                              output_target,
                              discard_matfile=discard_matfile)
    elif mode == 'octave':
        msg = ls.octave_solve(matfile_path,
                              output_target,
                              discard_matfile=discard_matfile)
    elif mode == 'neos':
        import solve_neos as ns
        msg = ns.neos_solve(matfile_path,
                            output_target=output_target,
                            discard_matfile=discard_matfile)

    # Process the message
    result = res.make_result_dict(msg)
    print "\nResult summary:\n" + res.make_result_summary(result)
    return result
