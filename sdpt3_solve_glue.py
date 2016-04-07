#!/usr/bin/env python
import os

import subprocess
import shlex

import sdpt3_writer as sw
import result as res

class MatlabCallError(Exception):
    pass


def solve_with_SDPT3(P, matfile_target, output_target, discard_matfile = True):
    '''
    Inputs:
      P: a cvxpy problem
      matfile_target: the absolute path we will save the .mat file to.
      output_target: the absolute path we will save the output log message to.
      discard_matfile: if True, deletes the .mat file after the solve finishes.
    Output:
        A dictionary with solve result information.
    '''
    # Generating the .mat file
    P_data = P.get_problem_data('CVXOPT')
    sw.write_sedumi_model(P_data, matfile_target)
    run_command = "matlab -r \"SDPT3solve('{0}')\"".format(matfile_target)
    msg = run_matlab_get_output(run_command, output_target)
    
    result = res.make_result_dict(msg)

    # Cleanup
    if discard_matfile:
        print "now deleting {0}".format(matfile_target)
        os.remove(matfile_target)
    
    # Print a summary statement and return
    print "\n" + res.make_result_summary(result)
    return result


def run_matlab_get_output(run_command, output_target):
    '''
    Runs the command run_command, saves the output to output_target, and
    returns the output log.
    '''
    # Performing the Matlab solve
    run_command += " -nodisplay -nojvm > {0};".format(output_target)
    tokenized_command = shlex.split(run_command)
    try:
        proc = subprocess.Popen(tokenized_command)
        proc.wait()
    except:
        err_msg = ("Something went wrong with the Matlab command. The command "
                   "run was:\n{0}\nPlease check that the command looks good "
                   "and that the the folder containing SDPT3solve.m is in the "
                   "Matlab path.").format(run_command)
        raise MatlabCallError(err_msg)

    # Reading the log and returning its contents
    with open(output_target, 'r') as myfile:
        msg=myfile.read()

    return msg
