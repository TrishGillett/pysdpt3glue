# -*- coding: utf-8 -*-
"""
Created on Fri Apr  8 01:23:57 2016

@author: trish
"""

import os.path

import sedumi_writer as sw
import sdpt3_solve_glue as ls
import result as res

def sdpt3_solve(problem, mode, matfile_target, output_target=None, discard_matfile=True):
    '''
    A wrapper function that takes a cvxpy problem, makes the .mat file, solves
    it by NEOS or a local Matlab/SDPT3 installation, then constructs the result,
    prints it, and returns it.
    '''
    assert mode in ['matlab', 'octave', 'neos'], \
        "Please choose mode equal to either 'matlab', 'octave', or 'neos'."
    assert mode not in ['matlab', 'octave'] or output_target, \
        "If mode is 'matlab' or 'octave', an output_target must be provided."
    assert not os.path.exists(matfile_target), \
        "Something already exists at matfile_target, we won't overwrite it."
    assert not os.path.exists(output_target), \
        "Something already exists at output_target, we won't overwrite it."

    # Write the problem to a .mat file in Sedumi format
    problem_data = problem.get_problem_data('CVXOPT')
    sw.write_sedumi_model(problem_data, matfile_target)

    # Depending on the mode, solve the problem using a local Matlab+SDPT3
    # installation or on the NEOS server
    if mode == 'matlab':
        msg = ls.matlab_solve(matfile_target,
                              output_target,
                              discard_matfile=discard_matfile)
    elif mode == 'octave':
        msg = ls.octave_solve(matfile_target,
                              output_target,
                              discard_matfile=discard_matfile)
    elif mode == 'neos':
        import sdpt3_solve_on_neos as ns
        msg = ns.neos_solve(matfile_target,
                            output_target=output_target,
                            discard_matfile=discard_matfile)

    # Process the message
    result = res.make_result_dict(msg)
    print "\n" + res.make_result_summary(result)
    return result
