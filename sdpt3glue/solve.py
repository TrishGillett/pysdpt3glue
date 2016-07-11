"""

"""

import os.path

import sedumi_writer as sw
import solve_locally as ls
import result as res


MATLAB = 'matlab'
OCTAVE = 'octave'
NEOS = 'neos'


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


def sdpt3_solve_problem(
        problem, mode, matfile_target,
        output_target=None, discard_matfile=True, **kwargs):
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
                           discard_matfile=discard_matfile,
                           **kwargs)


def sdpt3_solve_mat(
        matfile_path, mode, output_target=None, discard_matfile=True, **kwargs):
    '''
    A wrapper function that takes the path of a .mat file, solves the Sedumi
    problem it contains with NEOS or a local Matlab/SDPT3 installation, then
    constructs the result, prints it, and returns it.
    '''
    matfile_path = os.path.abspath(matfile_path)
    check_output_target(mode, output_target)

    # Depending on the mode, solve the problem using a local Matlab+SDPT3
    # installation or on the NEOS server
    if mode == MATLAB:
        msg = ls.matlab_solve(matfile_path,
                              discard_matfile=discard_matfile)
    elif mode == OCTAVE:
        msg = ls.octave_solve(matfile_path,
                              discard_matfile=discard_matfile,
                              **kwargs)
    elif mode == NEOS:
        import solve_neos as ns
        msg = ns.neos_solve(matfile_path,
                            discard_matfile=discard_matfile)

    if output_target:
        with open(output_target, "w") as fp:
            fp.write(msg)

    result = res.make_result_dict(msg)
    return result
